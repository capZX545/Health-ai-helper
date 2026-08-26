package com.nexusmed2077;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.os.Handler;
import android.os.Looper;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

/**
 * NexusMed 2077 — Android launcher.
 * Starts a local HTTP server that serves the bundled web app
 * and opens it in a full-screen WebView.
 */
public class MainActivity extends Activity {

    private WebView webView;
    private MiniServer server;
    private static final int PORT = 8080;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // copy assets to internal storage on first run
        copyAssetsIfNeeded();

        // start local server
        server = new MiniServer(PORT);
        new Thread(server).start();

        // wait a moment for server, then show WebView
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            webView = new WebView(MainActivity.this);
            WebSettings ws = webView.getSettings();
            ws.setJavaScriptEnabled(true);
            ws.setDomStorageEnabled(true);
            ws.setAllowFileAccess(true);
            ws.setLoadWithOverviewMode(true);
            ws.setUseWideViewPort(true);
            ws.setTextZoom(100);
            webView.setWebViewClient(new WebViewClient());
            setContentView(webView);
            webView.loadUrl("http://127.0.0.1:" + PORT + "/");
        }, 500);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (server != null) server.stop();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private void copyAssetsIfNeeded() {
        File dataDir = new File(getFilesDir(), "www");
        if (!dataDir.exists() || dataDir.listFiles().length == 0) {
            dataDir.mkdirs();
            try {
                String[] files = getAssets().list("www");
                if (files != null) {
                    for (String f : files) {
                        copyAsset("www/" + f, new File(dataDir, f));
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private void copyAsset(String assetPath, File dest) throws IOException {
        try (InputStream is = getAssets().open(assetPath);
             FileOutputStream fos = new FileOutputStream(dest)) {
            byte[] buf = new byte[8192];
            int len;
            while ((len = is.read(buf)) > 0) fos.write(buf, 0, len);
        }
    }

    /**
     * Minimal HTTP server that serves static files from internal storage.
     */
    static class MiniServer implements Runnable {
        private final int port;
        private volatile boolean running = true;
        private ServerSocket serverSocket;

        MiniServer(int port) { this.port = port; }

        @Override
        public void run() {
            try {
                serverSocket = new ServerSocket(port, 10, InetAddress.getByName("127.0.0.1"));
                while (running) {
                    Socket client = serverSocket.accept();
                    handle(client);
                }
            } catch (Exception e) {
                // server stopped
            }
        }

        void stop() {
            running = false;
            try { if (serverSocket != null) serverSocket.close(); } catch (IOException ignored) {}
        }

        private void handle(Socket client) {
            try (BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                 OutputStream out = client.getOutputStream()) {
                String line = in.readLine();
                if (line == null) return;
                String path = line.split(" ")[1];
                if (path.equals("/")) path = "/clinic_2077.html";

                // serve from /data/data/com.nexusmed2077/files/www/
                File wwwDir = new File("/data/data/com.nexusmed2077/files/www");
                File f = new File(wwwDir, path.substring(1));
                if (f.exists() && f.isFile()) {
                    byte[] data = readFile(f);
                    String mime = getMime(path);
                    out.write(("HTTP/1.0 200 OK\r\nContent-Type: " + mime + "\r\nContent-Length: " + data.length + "\r\nAccess-Control-Allow-Origin: *\r\n\r\n").getBytes());
                    out.write(data);
                } else {
                    out.write("HTTP/1.0 404 Not Found\r\nContent-Type: text/plain\r\n\r\nNot found".getBytes());
                }
            } catch (Exception ignored) {
            }
        }

        private byte[] readFile(File f) throws IOException {
            byte[] data = new byte[(int) f.length()];
            try (FileInputStream fis = new FileInputStream(f)) {
                fis.read(data);
            }
            return data;
        }

        private String getMime(String path) {
            if (path.endsWith(".html")) return "text/html; charset=utf-8";
            if (path.endsWith(".js")) return "application/javascript";
            if (path.endsWith(".css")) return "text/css";
            if (path.endsWith(".json")) return "application/json";
            if (path.endsWith(".svg")) return "image/svg+xml";
            if (path.endsWith(".gz")) return "application/gzip";
            if (path.endsWith(".png")) return "image/png";
            return "application/octet-stream";
        }
    }
}
