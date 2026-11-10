package com.tharunbirla.librecuts

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import android.os.Parcelable
import android.widget.TextView
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.tharunbirla.librecuts.databinding.ActivityMainBinding
import com.tharunbirla.librecuts.utils.ErrorCode
import com.tharunbirla.librecuts.utils.setBounceClickListener
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.speech.tts.TextToSpeech
import java.util.Locale
import com.tharunbirla.librecuts.utils.PersistentVaultManager

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var nativeTtsEngine: TextToSpeech? = null
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null
    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            val intent = result.data
            val uris = WebChromeClient.FileChooserParams.parseResult(result.resultCode, intent)
            fileChooserCallback?.onReceiveValue(uris)
        } else {
            fileChooserCallback?.onReceiveValue(null)
        }
        fileChooserCallback = null
    }
    private val selectVideoLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val takeFlags = Intent.FLAG_GRANT_READ_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)
                } catch (e: Exception) {
                    Log.e("VideoSelection", "Could not take persistable permission", e)
                }
                Log.d("VideoSelection", "Video selected: $uri")
                navigateToEditingScreen(uri)
            } else {
                Log.e("VideoSelectionError", "No video selected")
            }
        }

    private val openProjectLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val takeFlags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)
                } catch (e: Exception) {
                    Log.e("ProjectSelection", "Could not take persistable permission for project URI", e)
                }
                Log.d("ProjectSelection", "Project selected: $uri")
                val intent = Intent(this, ProjectImportActivity::class.java).apply {
                    putExtra("PROJECT_URI", uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                }
                startActivity(intent)
            } else {
                Log.e("ProjectSelectionError", "No project selected")
            }
        }

    private val selectFolderLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val takeFlags: Int = Intent.FLAG_GRANT_READ_URI_PERMISSION or
                            Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)

                    val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
                    prefs.edit().putString("export_directory_uri", uri.toString()).apply()
                    updateExportFolderUI(uri, binding.tvCurrentExportFolder, R.string.str_default_movies_librecuts)
                } catch (e: Exception) {
                    Log.e("FolderSelectionError", "Error securing permission for URI", e)
                    showToast(getString(R.string.toast_failed_to_set_export_folder))
                }
            }
        }

    private val selectAudioFolderLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val takeFlags: Int = Intent.FLAG_GRANT_READ_URI_PERMISSION or
                            Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)

                    val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
                    prefs.edit().putString("export_audio_directory_uri", uri.toString()).apply()
                    updateExportFolderUI(uri, binding.tvCurrentAudioExportFolder, R.string.str_default_music_librecuts)
                } catch (e: Exception) {
                    Log.e("FolderSelectionError", "Error securing permission for URI", e)
                    showToast(getString(R.string.toast_failed_to_set_export_folder))
                }
            }
        }

    private val selectSnapshotFolderLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val takeFlags: Int = Intent.FLAG_GRANT_READ_URI_PERMISSION or
                            Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)

                    val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
                    prefs.edit().putString("export_snapshot_directory_uri", uri.toString()).apply()
                    updateExportFolderUI(uri, binding.tvCurrentSnapshotExportFolder, R.string.str_default_pictures_librecuts)
                } catch (e: Exception) {
                    Log.e("FolderSelectionError", "Error securing permission for URI", e)
                    showToast(getString(R.string.toast_failed_to_set_export_folder))
                }
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnImport.setBounceClickListener {
            Log.d("ButtonClick", "Launching video selection.")
            selectVideo()
        }

        binding.btnOpenProject.setBounceClickListener {
            Log.d("ButtonClick", "Launching project selection.")
            openProjectLauncher.launch(arrayOf("*/*"))
        }

        // Initialize bottom navigation tab backgrounds
        val attrs = intArrayOf(android.R.attr.selectableItemBackgroundBorderless)
        val ta = obtainStyledAttributes(attrs)
        val inactiveBg = ta.getDrawable(0)
        ta.recycle()
        binding.tabSettings.background = inactiveBg
        binding.tabAbout.background = inactiveBg

        // Setup bottom navigation tab switching
        binding.tabHome.setBounceClickListener {
            switchTab(0)
        }

        binding.tabStudio.setBounceClickListener {
            selectVideo()
        }
        
        binding.tabSettings.setBounceClickListener {
            switchTab(2)
        }

        binding.tabAbout.setBounceClickListener {
            switchTab(3)
        }

        // Setup Apple Quick Action Cards on Home Dashboard
        binding.cardSubtitles.setBounceClickListener {
            openStudioTab("subtitles")
        }

        binding.cardTts.setBounceClickListener {
            openStudioTab("tts")
        }

        binding.cardPdf.setBounceClickListener {
            openStudioTab("pdf")
        }

        binding.cardAudio.setBounceClickListener {
            openStudioTab("audio")
        }

        binding.cardDownloader.setBounceClickListener {
            openStudioTab("downloader")
        }

        binding.cardFoto.setBounceClickListener {
            openStudioTab("foto")
        }
        
        // Setup Settings Actions
        binding.btnChangeExportFolder.setBounceClickListener {
            selectFolderLauncher.launch(null)
        }
        binding.btnChangeAudioExportFolder.setBounceClickListener {
            selectAudioFolderLauncher.launch(null)
        }
        binding.btnChangeSnapshotExportFolder.setBounceClickListener {
            selectSnapshotFolderLauncher.launch(null)
        }
        binding.btnChangeLanguage.setBounceClickListener {
            showLanguageDialog()
        }
        
        binding.btnCheckForUpdates.setBounceClickListener {
            checkForUpdates()
        }
        
        binding.btnOpenSourceLicenses.setBounceClickListener {
            com.mikepenz.aboutlibraries.LibsBuilder()
                .withActivityTitle(getString(R.string.str_open_source_licenses))
                .withSearchEnabled(true)
                .start(this)
        }
        
        // Initialize Settings UI
        val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
        val savedUriString = prefs.getString("export_directory_uri", null)
        if (savedUriString != null) {
            updateExportFolderUI(Uri.parse(savedUriString), binding.tvCurrentExportFolder, R.string.str_default_movies_librecuts)
        } else {
            updateExportFolderUI(null, binding.tvCurrentExportFolder, R.string.str_default_movies_librecuts)
        }

        val savedAudioUriString = prefs.getString("export_audio_directory_uri", null)
        if (savedAudioUriString != null) {
            updateExportFolderUI(Uri.parse(savedAudioUriString), binding.tvCurrentAudioExportFolder, R.string.str_default_music_librecuts)
        } else {
            updateExportFolderUI(null, binding.tvCurrentAudioExportFolder, R.string.str_default_music_librecuts)
        }

        val savedSnapshotUriString = prefs.getString("export_snapshot_directory_uri", null)
        if (savedSnapshotUriString != null) {
            updateExportFolderUI(Uri.parse(savedSnapshotUriString), binding.tvCurrentSnapshotExportFolder, R.string.str_default_pictures_librecuts)
        } else {
            updateExportFolderUI(null, binding.tvCurrentSnapshotExportFolder, R.string.str_default_pictures_librecuts)
        }

        updateLanguageUI()

        // Initialize Haptic Feedback preference
        updateHapticFeedbackUI()

        binding.btnToggleHapticFeedback.setBounceClickListener {
            val current = prefs.getBoolean("haptic_feedback", true)
            prefs.edit().putBoolean("haptic_feedback", !current).apply()
            updateHapticFeedbackUI()
        }

        // Initialize Fullscreen Editor preference
        updateFullscreenEditorUI()

        binding.btnToggleFullscreenEditor.setBounceClickListener {
            val current = prefs.getBoolean("fullscreen_editor", true)
            prefs.edit().putBoolean("fullscreen_editor", !current).apply()
            updateFullscreenEditorUI()
        }

        // Initialize Default Encoder preference
        updateEncoderUI()

        binding.btnChangeDefaultEncoder.setBounceClickListener {
            showEncoderDialog()
        }

        binding.cardPersistentVault.setBounceClickListener {
            showPersistentVaultDialog()
        }

        // Set dynamic About version tag
        try {
            val pInfo = packageManager.getPackageInfo(packageName, 0)
            binding.tvAboutVersion.text = "v${pInfo.versionName}"
        } catch (e: Exception) {
            binding.tvAboutVersion.text = "v1.0-beta5"
        }

        // Setup Social, Pix and Support listeners
        binding.btnStarGithub.setBounceClickListener {
            openUrl("https://www.instagram.com/coachmontanha/")
        }
        binding.btnTranslate.setBounceClickListener {
            openUrl("https://wa.me/5583999259385")
        }
        binding.btnReportBug.setBounceClickListener {
            openUrl("https://github.com/Coach-Montanha/montanha-media-lab/issues")
        }
        binding.btnSponsor.setBounceClickListener {
            copyPixKey()
        }

        // Onboarding / Welcome Dialog
        val isFirstLaunch = prefs.getBoolean("first_launch_v1", true)
        if (isFirstLaunch) {
            showOnboardingDialog(prefs)
        }

        // Handle shared/intent videos
        handleIntent(intent)

        // Pre-warm the studio WebView in background so tools open instantaneously without delay
        binding.webViewStudio.post {
            loadStudioIfNeeded()
        }
    }

    private fun updateExportFolderUI(uri: Uri?, textView: TextView, defaultStringResId: Int) {
        if (uri == null) {
            textView.text = getString(defaultStringResId)
        } else {
            try {
                val path = uri.lastPathSegment?.split(":")?.lastOrNull()
                if (!path.isNullOrEmpty()) {
                    textView.text = path
                } else {
                    textView.text = getString(R.string.str_custom_directory)
                }
            } catch (e: Exception) {
                textView.text = getString(R.string.str_custom_directory)
            }
        }
    }

    private data class LanguageItem(
        val tag: String,
        val displayName: String
    )

    private fun getAvailableLanguages(): List<LanguageItem> {
        val result = mutableListOf<LanguageItem>()
        result.add(LanguageItem("", getString(R.string.str_system_default)))

        val tags = mutableSetOf<String>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            try {
                val localeConfig = android.app.LocaleConfig(this)
                val locales = localeConfig.supportedLocales
                if (locales != null) {
                    for (i in 0 until locales.size()) {
                        val locale = locales.get(i)
                        if (locale != null) {
                            tags.add(locale.toLanguageTag())
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e("MainActivity", "LocaleConfig error", e)
            }
        }

        if (tags.isEmpty()) {
            try {
                val resId = resources.getIdentifier("_generated_res_locale_config", "xml", packageName)
                if (resId != 0) {
                    val parser = resources.getXml(resId)
                    var eventType = parser.eventType
                    while (eventType != org.xmlpull.v1.XmlPullParser.END_DOCUMENT) {
                        if (eventType == org.xmlpull.v1.XmlPullParser.START_TAG && parser.name == "locale") {
                            val name = parser.getAttributeValue("http://schemas.android.com/apk/res/android", "name")
                            if (!name.isNullOrEmpty()) {
                                tags.add(name)
                            }
                        }
                        eventType = parser.next()
                    }
                }
            } catch (e: Exception) {
                Log.e("MainActivity", "XmlParser _generated_res_locale_config error", e)
            }
        }

        if (tags.isEmpty()) {
            tags.addAll(listOf("en", "de", "et", "sk", "pt-BR"))
        }

        val items = tags.map { tag ->
            val locale = java.util.Locale.forLanguageTag(tag)
            val name = when (tag.lowercase()) {
                "pt-br" -> "Português (Brasil)"
                "zh-cn" -> "中文 (简体)"
                "zh-tw" -> "中文 (繁體)"
                else -> locale.getDisplayName(locale).replaceFirstChar { if (it.isLowerCase()) it.titlecase(locale) else it.toString() }
            }
            LanguageItem(tag, name)
        }.sortedBy { it.displayName.lowercase() }

        result.addAll(items)
        return result
    }

    private fun updateLanguageUI() {
        val currentLocales = AppCompatDelegate.getApplicationLocales()
        if (currentLocales.isEmpty) {
            binding.tvCurrentLanguage.text = getString(R.string.str_system_default)
        } else {
            val locale = currentLocales.get(0)
            val tag = locale?.toLanguageTag() ?: ""
            val name = when (tag.lowercase()) {
                "pt-br" -> "Português (Brasil)"
                else -> locale?.getDisplayName(locale)?.replaceFirstChar { if (it.isLowerCase()) it.titlecase(locale) else it.toString() }
            }
            binding.tvCurrentLanguage.text = name ?: getString(R.string.str_system_default)
        }
    }

    private fun updateHapticFeedbackUI() {
        val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
        val isEnabled = prefs.getBoolean("haptic_feedback", true)
        binding.tvCurrentHapticFeedback.text = if (isEnabled) {
            getString(R.string.str_haptic_enabled_desc)
        } else {
            getString(R.string.str_haptic_disabled_desc)
        }
    }

    private fun updateFullscreenEditorUI() {
        val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
        val isFullscreen = prefs.getBoolean("fullscreen_editor", true)
        binding.tvCurrentFullscreenEditor.text = if (isFullscreen) {
            getString(R.string.str_fullscreen_enabled_desc)
        } else {
            getString(R.string.str_fullscreen_disabled_desc)
        }
    }

    private fun updateEncoderUI() {
        val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
        val defaultEncoder = prefs.getString("default_encoder", "hardware") ?: "hardware"
        if (defaultEncoder == "software") {
            binding.tvCurrentDefaultEncoder.text = getString(R.string.str_encoder_software)
        } else {
            binding.tvCurrentDefaultEncoder.text = getString(R.string.str_encoder_hardware)
        }
    }

    private fun showEncoderDialog() {
        val prefs = getSharedPreferences("librecuts_prefs", MODE_PRIVATE)
        val currentEncoder = prefs.getString("default_encoder", "hardware") ?: "hardware"
        val options = arrayOf(
            getString(R.string.str_encoder_hardware),
            getString(R.string.str_encoder_software)
        )
        val selectedIndex = if (currentEncoder == "software") 1 else 0

        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.str_default_encoder)
            .setSingleChoiceItems(options, selectedIndex) { dialog, which ->
                val chosenEncoder = if (which == 1) "software" else "hardware"
                prefs.edit().putString("default_encoder", chosenEncoder).apply()
                updateEncoderUI()
                dialog.dismiss()
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun showLanguageDialog() {
        val dialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.language_bottom_sheet_dialog, null)
        dialog.setContentView(view)

        view.findViewById<View>(R.id.btnCloseSheet)?.setBounceClickListener {
            dialog.dismiss()
        }

        val container = view.findViewById<android.widget.LinearLayout>(R.id.layoutLanguageContainer)
        val currentLocales = AppCompatDelegate.getApplicationLocales()
        val currentTag = if (currentLocales.isEmpty) "" else (currentLocales.get(0)?.toLanguageTag() ?: "")

        val availableLanguages = getAvailableLanguages()

        for (item in availableLanguages) {
            val itemView = layoutInflater.inflate(R.layout.item_language_selection, container, false)
            val tvName = itemView.findViewById<TextView>(R.id.tvLanguageName)
            val ivCheck = itemView.findViewById<android.widget.ImageView>(R.id.ivCheckLanguage)

            tvName.text = item.displayName

            val isSelected = if (item.tag.isEmpty()) {
                currentTag.isEmpty()
            } else {
                currentTag.equals(item.tag, ignoreCase = true) ||
                (item.tag.length == 2 && currentTag.startsWith(item.tag, ignoreCase = true))
            }

            ivCheck.visibility = if (isSelected) View.VISIBLE else View.GONE

            itemView.setBounceClickListener {
                val appLocale = if (item.tag.isEmpty()) {
                    LocaleListCompat.getEmptyLocaleList()
                } else {
                    LocaleListCompat.forLanguageTags(item.tag)
                }
                AppCompatDelegate.setApplicationLocales(appLocale)
                updateLanguageUI()
                dialog.dismiss()
            }

            container?.addView(itemView)
        }

        dialog.show()
    }

    private var isStudioLoaded = false
    private var pendingStudioTab: String? = null

    private fun copyPixKey() {
        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
            val clip = android.content.ClipData.newPlainText("Chave Pix", "00891652418")
            clipboard.setPrimaryClip(clip)
            showToast("Chave Pix (00891652418) copiada!")
        } catch (e: Exception) {
            showToast("Chave Pix: 00891652418")
        }
    }

    private fun loadStudioIfNeeded() {
        if (!isStudioLoaded) {
            binding.webViewStudio.setBackgroundColor(android.graphics.Color.TRANSPARENT)
            binding.layoutStudioContent.setBackgroundColor(android.graphics.Color.parseColor("#0B0C0E"))
            binding.webViewStudio.settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                allowFileAccess = true
                allowContentAccess = true
                allowFileAccessFromFileURLs = true
                allowUniversalAccessFromFileURLs = true
                mediaPlaybackRequiresUserGesture = false
                databaseEnabled = true
            }

            nativeTtsEngine = TextToSpeech(this@MainActivity) { status ->
                if (status == TextToSpeech.SUCCESS) {
                    nativeTtsEngine?.language = Locale("pt", "BR")
                }
            }

            // Bridge to allow webview tool headers to navigate back to native home and use native TTS
            binding.webViewStudio.addJavascriptInterface(object {
                @android.webkit.JavascriptInterface
                fun goNativeHome() {
                    runOnUiThread {
                        switchTab(0)
                    }
                }

                @android.webkit.JavascriptInterface
                fun openNativeVideoEditor() {
                    runOnUiThread {
                        selectVideo()
                    }
                }

                @android.webkit.JavascriptInterface
                fun speakText(text: String) {
                    runOnUiThread {
                        speakTextWithVoice(text, null, 1.0f)
                    }
                }

                @android.webkit.JavascriptInterface
                fun speakTextWithVoice(text: String, voiceName: String?, rate: Float) {
                    runOnUiThread {
                        this@MainActivity.speakTextWithVoice(text, voiceName, rate)
                    }
                }

                @android.webkit.JavascriptInterface
                fun saveAccountData(key: String, value: String) {
                    PersistentVaultManager.saveCredential(this@MainActivity, key, value)
                }

                @android.webkit.JavascriptInterface
                fun getAccountData(key: String): String {
                    return PersistentVaultManager.getCredential(this@MainActivity, key, "")
                }

                @android.webkit.JavascriptInterface
                fun getClipboardText(): String {
                    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as? android.content.ClipboardManager
                    val clip = clipboard?.primaryClip
                    if (clip != null && clip.itemCount > 0) {
                        return clip.getItemAt(0).text?.toString() ?: ""
                    }
                    return ""
                }

                @android.webkit.JavascriptInterface
                fun downloadSocialMedia(url: String, format: String) {
                    runOnUiThread {
                        showToast("Iniciando download interno na pasta Downloads...")
                    }
                    lifecycleScope.launch(Dispatchers.IO) {
                        try {
                            var directMediaUrl: String? = null
                            var outputFilename = "social_media_${System.currentTimeMillis()}.${if (format == "audio") "mp3" else "mp4"}"

                            // 1. Tentar resolver via servidor local (se ativo no dispositivo)
                            try {
                                val srvUrl = URL("http://127.0.0.1:4190/api/import-cloud-url")
                                val conn = srvUrl.openConnection() as HttpURLConnection
                                conn.connectTimeout = 1500
                                conn.readTimeout = 60000
                                conn.requestMethod = "POST"
                                conn.doOutput = true
                                conn.setRequestProperty("Content-Type", "application/json")
                                val jsonBody = JSONObject().apply {
                                    put("url", url)
                                    put("formato", format)
                                }
                                conn.outputStream.write(jsonBody.toString().toByteArray())
                                if (conn.responseCode == 200) {
                                    val respText = conn.inputStream.bufferedReader().readText()
                                    val respJson = JSONObject(respText)
                                    if (respJson.optString("status") == "success") {
                                        withContext(Dispatchers.Main) {
                                            showToast("✓ Vídeo baixado localmente na pasta Downloads!")
                                        }
                                        return@launch
                                    }
                                }
                            } catch (_: Exception) {}

                            // 2. Resolver em segundo plano via endpoints diretos de extração (zero redirect para navegador)
                            val endpoints = listOf(
                                "https://cobalt-api.kwiatekm.pl/api/json",
                                "https://api.cobalt.tools/api/json"
                            )
                            for (api in endpoints) {
                                try {
                                    val u = URL(api)
                                    val conn = u.openConnection() as HttpURLConnection
                                    conn.connectTimeout = 4000
                                    conn.readTimeout = 20000
                                    conn.requestMethod = "POST"
                                    conn.doOutput = true
                                    conn.setRequestProperty("Content-Type", "application/json")
                                    conn.setRequestProperty("Accept", "application/json")
                                    val payload = JSONObject().apply {
                                        put("url", url)
                                        put("downloadMode", if (format == "audio") "audio" else "auto")
                                    }
                                    conn.outputStream.write(payload.toString().toByteArray())
                                    if (conn.responseCode == 200) {
                                        val resp = JSONObject(conn.inputStream.bufferedReader().readText())
                                        val fetchedUrl = resp.optString("url")
                                        if (fetchedUrl.isNotEmpty()) {
                                            directMediaUrl = fetchedUrl
                                            resp.optString("filename").let { fn ->
                                                if (fn.isNotEmpty()) outputFilename = fn
                                            }
                                            break
                                        }
                                    }
                                } catch (_: Exception) {}
                            }

                            if (!directMediaUrl.isNullOrEmpty()) {
                                withContext(Dispatchers.Main) {
                                    try {
                                        val dm = getSystemService(Context.DOWNLOAD_SERVICE) as android.app.DownloadManager
                                        val req = android.app.DownloadManager.Request(Uri.parse(directMediaUrl)).apply {
                                            setTitle(outputFilename)
                                            setDescription("Montanha Media Lab - Download Concluído")
                                            setNotificationVisibility(android.app.DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                                            setDestinationInExternalPublicDir(android.os.Environment.DIRECTORY_DOWNLOADS, outputFilename)
                                            setAllowedOverMetered(true)
                                            setAllowedOverRoaming(true)
                                        }
                                        dm.enqueue(req)
                                        showToast("✓ Download iniciado em segundo plano na pasta Downloads!")
                                    } catch (e: Exception) {
                                        showToast("Erro ao agendar download: ${e.message}")
                                    }
                                }
                            } else {
                                withContext(Dispatchers.Main) {
                                    showToast("Não foi possível extrair a mídia diretamente. Verifique se o link é público.")
                                }
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) {
                                showToast("Falha no download direto: ${e.message}")
                            }
                        }
                    }
                }

                @android.webkit.JavascriptInterface
                fun syncVault() {
                    PersistentVaultManager.syncPrefsToVault(this@MainActivity)
                }
            }, "AndroidBridge")

            binding.webViewStudio.webViewClient = object : android.webkit.WebViewClient() {
                override fun onPageFinished(view: android.webkit.WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    pendingStudioTab?.let { tab ->
                        binding.webViewStudio.evaluateJavascript(
                            "if (typeof switchAppTab === 'function') switchAppTab('$tab');",
                            null
                        )
                        pendingStudioTab = null
                    }
                }
            }
            binding.webViewStudio.webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    webView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams?
                ): Boolean {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = filePathCallback
                    val intent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                        type = "*/*"
                        addCategory(Intent.CATEGORY_OPENABLE)
                    }
                    try {
                        fileChooserLauncher.launch(intent)
                        return true
                    } catch (e: Exception) {
                        fileChooserCallback = null
                        return false
                    }
                }
            }
            binding.webViewStudio.loadUrl("file:///android_asset/studio/index.html")
            isStudioLoaded = true
        }
    }

    private fun openStudioTab(tabKey: String) {
        pendingStudioTab = tabKey
        loadStudioIfNeeded()
        if (isStudioLoaded) {
            binding.webViewStudio.evaluateJavascript(
                "if (typeof switchAppTab === 'function') switchAppTab('$tabKey');",
                null
            )
        }
        switchTab(1)
    }

    private fun switchTab(tabIndex: Int) {
        val activeBg = ContextCompat.getDrawable(this, R.drawable.bg_nav_active_pill)
        val attrs = intArrayOf(android.R.attr.selectableItemBackgroundBorderless)
        val ta = obtainStyledAttributes(attrs)
        val inactiveBg = ta.getDrawable(0)
        ta.recycle()

        val activeColor = ContextCompat.getColor(this, R.color.colorPrimary)
        val inactiveColor = ContextCompat.getColor(this, R.color.inactiveTool)

        val targetView = when (tabIndex) {
            0 -> binding.layoutHomeContent
            1 -> binding.layoutStudioContent
            2 -> binding.layoutSettingsContent
            3 -> binding.layoutAboutContent
            else -> binding.layoutHomeContent
        }

        val allViews = listOf(
            binding.layoutHomeContent,
            binding.layoutStudioContent,
            binding.layoutSettingsContent,
            binding.layoutAboutContent
        )

        allViews.forEach { v ->
            if (v != targetView && v.visibility == View.VISIBLE) {
                v.visibility = View.GONE
                v.alpha = 1f
            }
        }

        binding.tabHome.background = inactiveBg
        binding.ivHome.setColorFilter(inactiveColor)
        binding.tvHomeLabel.setTextColor(inactiveColor)

        binding.tabStudio.background = inactiveBg
        binding.ivStudio.setColorFilter(inactiveColor)
        binding.tvStudioLabel.setTextColor(inactiveColor)

        binding.tabSettings.background = inactiveBg
        binding.ivSettings.setColorFilter(inactiveColor)
        binding.tvSettingsLabel.setTextColor(inactiveColor)

        binding.tabAbout.background = inactiveBg
        binding.ivAbout.setColorFilter(inactiveColor)
        binding.tvAboutLabel.setTextColor(inactiveColor)

        when (tabIndex) {
            0 -> {
                binding.tabHome.background = activeBg
                binding.ivHome.setColorFilter(activeColor)
                binding.tvHomeLabel.setTextColor(activeColor)
            }
            1 -> {
                binding.tabStudio.background = activeBg
                binding.ivStudio.setColorFilter(activeColor)
                binding.tvStudioLabel.setTextColor(activeColor)
                loadStudioIfNeeded()
            }
            2 -> {
                binding.tabSettings.background = activeBg
                binding.ivSettings.setColorFilter(activeColor)
                binding.tvSettingsLabel.setTextColor(activeColor)
            }
            3 -> {
                binding.tabAbout.background = activeBg
                binding.ivAbout.setColorFilter(activeColor)
                binding.tvAboutLabel.setTextColor(activeColor)
            }
        }

        targetView.alpha = 0.4f
        targetView.visibility = View.VISIBLE
        targetView.animate().alpha(1f).setDuration(120).start()
    }

    private fun speakTextWithVoice(text: String, voiceName: String? = null, rate: Float = 1.0f) {
        val tts = nativeTtsEngine ?: return
        try {
            tts.setSpeechRate(if (rate > 0f) rate else 1.0f)
            val isMale = voiceName?.contains("antonio", ignoreCase = true) == true ||
                         voiceName?.contains("masculino", ignoreCase = true) == true
            val isYoungFemale = voiceName?.contains("thalita", ignoreCase = true) == true

            if (isMale) {
                tts.setPitch(0.80f)
            } else if (isYoungFemale) {
                tts.setPitch(1.15f)
            } else {
                tts.setPitch(1.0f)
            }

            val voices = tts.voices
            if (!voices.isNullOrEmpty()) {
                val ptVoices = voices.filter { it.locale.language == "pt" }
                val targetVoice = if (isMale) {
                    ptVoices.firstOrNull { 
                        it.name.contains("male", ignoreCase = true) || 
                        it.name.contains("pt-br-x-afs#male", ignoreCase = true) ||
                        it.name.contains("pt-br-x-jab", ignoreCase = true) ||
                        it.name.contains("pt-br-x-jbc", ignoreCase = true) ||
                        it.name.contains("pt-br-x-jbd", ignoreCase = true)
                    } ?: ptVoices.firstOrNull()
                } else {
                    ptVoices.firstOrNull { 
                        it.name.contains("female", ignoreCase = true) || 
                        it.name.contains("pt-br-x-afs#female", ignoreCase = true) ||
                        it.name.contains("pt-br-x-sfg", ignoreCase = true)
                    } ?: ptVoices.firstOrNull()
                }
                if (targetVoice != null) {
                    tts.voice = targetVoice
                }
            }

            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "TTS_STUDIO")
            val label = if (isMale) "Masculina (Antonio)" else if (isYoungFemale) "Feminina (Thalita)" else "Feminina (Francisca)"
            showToast("✓ Reproduzindo voz [$label]")
        } catch (e: Exception) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "TTS_STUDIO")
        }
    }

    override fun onDestroy() {
        nativeTtsEngine?.stop()
        nativeTtsEngine?.shutdown()
        nativeTtsEngine = null
        super.onDestroy()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (binding.layoutStudioContent.visibility == View.VISIBLE) {
            if (binding.webViewStudio.canGoBack()) {
                binding.webViewStudio.goBack()
            } else {
                switchTab(0)
            }
        } else {
            super.onBackPressed()
        }
    }

    private fun openUrl(url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            startActivity(intent)
        } catch (e: Exception) {
            showToast("Unable to open link")
        }
    }





    private fun selectVideo() {
        Log.d("VideoSelection", "Launching video picker.")
        val picker = com.tharunbirla.librecuts.customviews.MediaPickerBottomSheet().apply {
            initialMediaType = com.tharunbirla.librecuts.customviews.MediaPickerBottomSheet.MediaType.VIDEO
            showCategoryTabs = true
            showAudioTab = false
            onMediaSelectedListener = { uri ->
                try {
                    val takeFlags = Intent.FLAG_GRANT_READ_URI_PERMISSION
                    contentResolver.takePersistableUriPermission(uri, takeFlags)
                } catch (e: Exception) {
                    Log.d("VideoSelection", "Could not take persistable permission: ${e.message}")
                }
                navigateToEditingScreen(uri)
            }
            onBrowseSystemFoldersRequested = {
                selectVideoLauncher.launch(arrayOf("video/*", "image/*"))
            }
        }
        picker.show(supportFragmentManager, "MediaPickerBottomSheet")
    }

    private fun navigateToEditingScreen(videoUri: Uri) {
        Log.d("Navigation", "Navigating to editing screen with URI: $videoUri")
        val intent = Intent(this, VideoEditingActivity::class.java).apply {
            putExtra("VIDEO_URI", videoUri)
            data = videoUri
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        if (intent == null) return
        val action = intent.action
        val type = intent.type

        if (Intent.ACTION_SEND == action && type != null) {
            if (type.startsWith("video/") || type.startsWith("image/")) {
                (intent.getParcelableExtra<Parcelable>(Intent.EXTRA_STREAM) as? Uri)?.let { uri ->
                    Log.d("SharedVideo", "Received SEND intent with media URI: $uri")
                    navigateToEditingScreen(uri)
                }
            }
        } else if ((Intent.ACTION_VIEW == action || Intent.ACTION_EDIT == action) && type != null) {
            if (type.startsWith("video/") || type.startsWith("image/")) {
                intent.data?.let { uri ->
                    Log.d("SharedVideo", "Received VIEW/EDIT intent with media URI: $uri")
                    navigateToEditingScreen(uri)
                }
            }
        }
    }

    private fun showOnboardingDialog(prefs: android.content.SharedPreferences) {
        val dialog = android.app.Dialog(this)
        val view = layoutInflater.inflate(R.layout.dialog_welcome_onboarding, null)
        dialog.setContentView(view)
        dialog.setCancelable(false)

        dialog.window?.let { window ->
            // Make dialog window background transparent so our custom layout's background card and shape render perfectly
            window.setBackgroundDrawableResource(android.R.color.transparent)
            
            // Set size parameters
            val lp = window.attributes
            lp.width = android.view.ViewGroup.LayoutParams.MATCH_PARENT
            lp.height = android.view.ViewGroup.LayoutParams.WRAP_CONTENT
            window.attributes = lp
        }

        // Set version dynamically
        val tvVersion = view.findViewById<TextView>(R.id.tvOnboardingVersion)
        try {
            val pInfo = packageManager.getPackageInfo(packageName, 0)
            tvVersion.text = "Version ${pInfo.versionName}"
        } catch (e: Exception) {
            tvVersion.text = "Version 1.0-beta4"
        }

        view.findViewById<View>(R.id.layoutStarGithub)?.setBounceClickListener {
            openUrl("https://www.instagram.com/coachmontanha/")
        }

        view.findViewById<View>(R.id.layoutSponsorGithub)?.setBounceClickListener {
            copyPixKey()
        }

        view.findViewById<View>(R.id.layoutDiscord)?.setBounceClickListener {
            openUrl("https://wa.me/5583999259385")
        }

        view.findViewById<View>(R.id.layoutTroubleshooting)?.setBounceClickListener {
            openUrl("https://github.com/Coach-Montanha/montanha-media-lab/wiki/Error-Codes-&-Troubleshooting")
        }

        view.findViewById<View>(R.id.btnOnboardingGetStarted)?.setBounceClickListener {
            prefs.edit().putBoolean("first_launch_v1", false).apply()
            dialog.dismiss()
        }

        dialog.show()
    }

    private fun showToast(message: String) {
        Log.d("ToastMessage", "Showing toast: $message")
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }

    private fun showPersistentVaultDialog() {
        val dialog = BottomSheetDialog(this)
        val container = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(40, 36, 40, 48)
            setBackgroundColor(android.graphics.Color.parseColor("#141720"))
        }

        val title = TextView(this).apply {
            text = "Login & Backup Permanente"
            textSize = 18f
            setTextColor(android.graphics.Color.WHITE)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 8)
        }
        container.addView(title)

        val desc = TextView(this).apply {
            text = "As informações salvas aqui ficam gravadas no armazenamento permanente do telefone (Documentos/MontanhaMediaLab/.vault/) com criptografia AES-256 e retornam automaticamente mesmo se você desinstalar o aplicativo."
            textSize = 12f
            setTextColor(android.graphics.Color.parseColor("#8E8E93"))
            setPadding(0, 0, 0, 20)
        }
        container.addView(desc)

        val currentEmail = PersistentVaultManager.getCredential(this, "user_email", "")
        val currentToken = PersistentVaultManager.getCredential(this, "user_token", "")

        val tvEmailLabel = TextView(this).apply {
            text = "Usuário / E-mail / Identificador"
            textSize = 13f
            setTextColor(android.graphics.Color.WHITE)
            setPadding(0, 0, 0, 6)
        }
        container.addView(tvEmailLabel)

        val inputEmail = android.widget.EditText(this).apply {
            hint = "ex: coach@montanha.com"
            setHintTextColor(android.graphics.Color.parseColor("#8E8E93"))
            setTextColor(android.graphics.Color.WHITE)
            textSize = 14f
            setText(currentEmail)
            setPadding(24, 20, 24, 20)
            setBackgroundResource(R.drawable.bg_aspect_ratio_item)
        }
        container.addView(inputEmail)

        val tvTokenLabel = TextView(this).apply {
            text = "Senha / Token de Acesso / Chave API"
            textSize = 13f
            setTextColor(android.graphics.Color.WHITE)
            setPadding(0, 16, 0, 6)
        }
        container.addView(tvTokenLabel)

        val inputToken = android.widget.EditText(this).apply {
            hint = "Senha da conta ou token"
            setHintTextColor(android.graphics.Color.parseColor("#8E8E93"))
            setTextColor(android.graphics.Color.WHITE)
            textSize = 14f
            transformationMethod = android.text.method.PasswordTransformationMethod.getInstance()
            setText(currentToken)
            setPadding(24, 20, 24, 20)
            setBackgroundResource(R.drawable.bg_aspect_ratio_item)
        }
        container.addView(inputToken)

        val btnSave = android.widget.Button(this).apply {
            text = "Salvar Credenciais no Cofre Permanente"
            textSize = 14f
            setTextColor(android.graphics.Color.WHITE)
            setBackgroundResource(R.drawable.bg_hero_bento_primary)
            val params = android.widget.LinearLayout.LayoutParams(android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 120).apply {
                topMargin = 24
            }
            layoutParams = params
            setOnClickListener {
                val email = inputEmail.text.toString().trim()
                val token = inputToken.text.toString().trim()
                PersistentVaultManager.saveUserAccount(this@MainActivity, email, email, token)
                Toast.makeText(this@MainActivity, "✓ Dados salvos permanentemente no telefone!", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
        }
        container.addView(btnSave)

        val btnRestore = android.widget.Button(this).apply {
            text = "Forçar Restauração do Arquivo do Telefone"
            textSize = 13f
            setTextColor(android.graphics.Color.parseColor("#2997FF"))
            setBackgroundColor(android.graphics.Color.TRANSPARENT)
            val params = android.widget.LinearLayout.LayoutParams(android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT).apply {
                topMargin = 8
            }
            layoutParams = params
            setOnClickListener {
                val ok = PersistentVaultManager.restoreFromVault(this@MainActivity)
                if (ok) {
                    Toast.makeText(this@MainActivity, "✓ Dados restaurados com sucesso!", Toast.LENGTH_SHORT).show()
                    val reloadedEmail = PersistentVaultManager.getCredential(this@MainActivity, "user_email", "")
                    val reloadedToken = PersistentVaultManager.getCredential(this@MainActivity, "user_token", "")
                    inputEmail.setText(reloadedEmail)
                    inputToken.setText(reloadedToken)
                } else {
                    Toast.makeText(this@MainActivity, "Nenhum arquivo de backup anterior encontrado.", Toast.LENGTH_SHORT).show()
                }
            }
        }
        container.addView(btnRestore)

        dialog.setContentView(container)
        dialog.show()
    }

    private fun checkForUpdates() {
        showToast("Checking for updates in browser...")
        openUrl("https://github.com/Coach-Montanha/montanha-media-lab/releases/latest")
    }
}