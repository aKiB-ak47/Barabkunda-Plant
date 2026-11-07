package com.bmenergy.barabkunda;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.core.splashscreen.SplashScreen;
import androidx.webkit.WebViewAssetLoader;

/**
 * BM Energy Barabkunda Plant app. Prepared by Akib Fateh.
 * Opens the live website so the plant data are always current; with no internet it shows the
 * last saved copy (website offline cache), or the copy built into the app.
 */
public class MainActivity extends Activity {
    static final String HOST = "akib-ak47.github.io";
    static final String LIVE = "https://" + HOST + "/Barabkunda-Plant/";
    static final String LOCAL_HOST = "appassets.androidplatform.net";
    static final String LOCAL = "https://" + LOCAL_HOST + "/assets/www/index.html";

    private WebView web;
    private WebViewAssetLoader loader;
    private boolean ready = false;
    private boolean usingLocal = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        SplashScreen splash = SplashScreen.installSplashScreen(this);
        super.onCreate(state);
        splash.setKeepOnScreenCondition(() -> !ready);
        new Handler(Looper.getMainLooper()).postDelayed(() -> ready = true, 5000);

        web = new WebView(this);
        web.setBackgroundColor(0xFF030812);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);   // the welcome music plays without a tap
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setCacheMode(online() ? WebSettings.LOAD_DEFAULT : WebSettings.LOAD_CACHE_ELSE_NETWORK);
        s.setUserAgentString(s.getUserAgentString() + " BMBarabkundaApp/" + versionName());

        loader = new WebViewAssetLoader.Builder()
                .setDomain(LOCAL_HOST)
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return loader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                String host = u.getHost() == null ? "" : u.getHost();
                String path = u.getPath() == null ? "" : u.getPath();
                if (host.equals(LOCAL_HOST)) return false;
                if (host.equals(HOST) && path.startsWith("/Barabkunda-Plant") && !path.endsWith(".apk")) return false;
                openOutside(u);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame() && !usingLocal) showLocal();
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
                if (request.isForMainFrame() && !usingLocal && response.getStatusCode() >= 500) showLocal();
            }

            @Override
            public void onPageCommitVisible(WebView view, String url) { ready = true; }

            @Override
            public void onPageFinished(WebView view, String url) { ready = true; }
        });

        if (state != null && web.restoreState(state) != null) return;
        web.loadUrl(startUrl(getIntent()));
    }

    private String startUrl(Intent intent) {
        Uri data = intent == null ? null : intent.getData();
        if (data != null && HOST.equals(data.getHost()) && data.getPath() != null && data.getPath().startsWith("/Barabkunda-Plant")) return data.toString();
        return LIVE;
    }

    private void showLocal() {
        usingLocal = true;
        web.loadUrl(LOCAL);
        Toast.makeText(this, R.string.offline_note, Toast.LENGTH_LONG).show();
    }

    private void openOutside(Uri u) {
        try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (ActivityNotFoundException ignored) { }
    }

    private boolean online() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
        if (cm == null) return true;
        NetworkCapabilities nc = cm.getNetworkCapabilities(cm.getActiveNetwork());
        return nc != null && nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }

    private String versionName() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(getPackageName(), 0);
            return p.versionName == null ? "1" : p.versionName;
        } catch (Exception e) { return "1"; }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (intent != null && intent.getData() != null) { usingLocal = false; web.loadUrl(startUrl(intent)); }
    }

    /** Back closes the open panel or report first, then leaves the app. */
    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        web.evaluateJavascript("(window.__appBack && window.__appBack()) ? 'y' : 'n'", v -> {
            if (v != null && v.contains("y")) return;
            if (web.canGoBack()) web.goBack(); else finish();
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onPause() { super.onPause(); web.onPause(); }

    @Override
    protected void onResume() { super.onResume(); web.onResume(); }

    @Override
    protected void onDestroy() {
        if (web != null) { web.stopLoading(); web.destroy(); }
        super.onDestroy();
    }
}
