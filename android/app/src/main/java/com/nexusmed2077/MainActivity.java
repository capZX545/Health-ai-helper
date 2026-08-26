package com.nexusmed2077;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.inputmethod.EditorInfo;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.widget.*;
import android.view.View;
import android.view.ViewGroup;
import android.view.Gravity;
import android.graphics.Color;

/**
 * NexusMed 2077 — Android app.
 * Connects to the deployed web server (Render.com).
 * First launch: asks for server URL, then opens full-screen WebView.
 * ALL features work because the Python backend runs on the server.
 */
public class MainActivity extends Activity {

    private WebView webView;
    private EditText urlInput;
    private LinearLayout setupView;
    private String serverUrl;
    private static final String PREFS = "nexusmed";
    private static final String KEY_URL = "server_url";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        serverUrl = prefs.getString(KEY_URL, "");

        if (serverUrl.isEmpty()) {
            showSetup();
        } else {
            showApp(serverUrl);
        }
    }

    private void showSetup() {
        setupView = new LinearLayout(this);
        setupView.setOrientation(LinearLayout.VERTICAL);
        setupView.setGravity(Gravity.CENTER);
        setupView.setBackgroundColor(Color.parseColor("#04060c"));
        setupView.setPadding(40, 40, 40, 40);

        // Title
        TextView title = new TextView(this);
        title.setText("NexusMed 2077");
        title.setTextSize(28);
        title.setTextColor(Color.parseColor("#00f0ff"));
        title.setGravity(Gravity.CENTER);
        setupView.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("دستیار پزشکی هوشمند\n\nEnter your server URL:\nآدرس سرور را وارد کنید:");
        subtitle.setTextSize(16);
        subtitle.setTextColor(Color.parseColor("#d7e3ff"));
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, 20, 0, 30);
        setupView.addView(subtitle);

        // URL input
        urlInput = new EditText(this);
        urlInput.setHint("https://nexusmed-2077.onrender.com");
        urlInput.setTextColor(Color.parseColor("#d7e3ff"));
        urlInput.setHintTextColor(Color.parseColor("#6b7fa3"));
        urlInput.setBackgroundColor(Color.parseColor("#0a1424"));
        urlInput.setPadding(20, 15, 20, 15);
        urlInput.setTextSize(16);
        urlInput.setSingleLine();
        urlInput.setImeActionLabel("Connect", EditorInfo.IME_ACTION_GO);
        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO) {
                connect();
                return true;
            }
            return false;
        });
        LinearLayout.LayoutParams urlParams = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        urlInput.setLayoutParams(urlParams);
        setupView.addView(urlInput);

        // Connect button
        Button connectBtn = new Button(this);
        connectBtn.setText("Connect / اتصال");
        connectBtn.setTextColor(Color.parseColor("#021018"));
        connectBtn.setBackgroundColor(Color.parseColor("#00b8d4"));
        connectBtn.setTextSize(18);
        connectBtn.setPadding(30, 20, 30, 20);
        connectBtn.setOnClickListener(v -> connect());
        LinearLayout.LayoutParams btnParams = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        btnParams.topMargin = 30;
        connectBtn.setLayoutParams(btnParams);
        setupView.addView(connectBtn);

        // Instructions
        TextView help = new TextView(this);
        help.setText("\n📱 How to get a server URL:\n\n1. Go to render.com (free)\n2. Deploy this GitHub repo\n3. Copy the URL here\n\nبرای دریافت آدرس سرور:\nروی render.com رایگان ثبت کن\nو آدرس را اینجا وارد کن");
        help.setTextSize(13);
        help.setTextColor(Color.parseColor("#6b7fa3"));
        help.setGravity(Gravity.CENTER);
        help.setPadding(0, 30, 0, 0);
        setupView.addView(help);

        setContentView(setupView);
    }

    private void connect() {
        String url = urlInput.getText().toString().trim();
        if (url.isEmpty()) {
            Toast.makeText(this, "Enter a URL / آدرس را وارد کن", Toast.LENGTH_SHORT).show();
            return;
        }
        // normalize
        if (!url.startsWith("http")) url = "https://" + url;
        if (url.endsWith("/")) url = url.substring(0, url.length() - 1);

        // save
        getSharedPreferences(PREFS, MODE_PRIVATE)
            .edit().putString(KEY_URL, url).apply();

        showApp(url);
    }

    private void showApp(String url) {
        webView = new WebView(this);
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setAllowFileAccess(true);
        ws.setLoadWithOverviewMode(true);
        ws.setUseWideViewPort(true);
        ws.setTextZoom(100);
        ws.setSupportZoom(false);
        ws.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                // inject mobile CSS tweaks if needed
                view.evaluateJavascript(
                    "if(document.querySelector('nav')){document.querySelector('nav').style.position='fixed';" +
                    "document.querySelector('nav').style.bottom='0';" +
                    "document.querySelector('nav').style.top='auto';" +
                    "document.querySelector('nav').style.flexDirection='row';" +
                    "document.querySelector('nav').style.overflowX='auto';" +
                    "document.querySelector('nav').style.width='100%';" +
                    "document.querySelector('nav').style.display='flex';" +
                    "document.querySelector('nav').style.padding='4px';}", null);
                super.onPageFinished(view, url);
            }
        });

        setContentView(webView);
        webView.loadUrl(url);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (webView != null) {
            webView.destroy();
        }
    }
}
