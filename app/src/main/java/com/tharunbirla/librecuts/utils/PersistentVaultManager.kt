package com.tharunbirla.librecuts.utils

import android.content.Context
import android.content.SharedPreferences
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.Base64
import android.util.Log
import android.widget.Toast
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * PersistentVaultManager
 * 
 * Garante que credenciais de login, senhas, tokens, dados da conta e preferências
 * do usuário permaneçam salvos permanentemente no armazenamento do telefone.
 * 
 * Mesmo que o aplicativo seja atualizado ou completamente desinstalado/excluído,
 * ao ser reinstalado, o Vault detecta o arquivo persistente em Documentos/MontanhaMediaLab/.vault/
 * e restaura todas as informações automaticamente sem intervenção manual.
 */
object PersistentVaultManager {

    private const val TAG = "PersistentVault"
    private const val PREFS_NAME = "librecuts_prefs"
    private const val VAULT_DIR_NAME = "MontanhaMediaLab/.vault"
    private const val VAULT_FILE_NAME = "montanha_profile.vault"
    private const val INTERNAL_SALT = "MontanhaMediaLab_Autonomous_Vault_Salt_2026_Key"

    private var isInitialized = false
    private var isRestoring = false

    fun init(context: Context) {
        if (isInitialized) return
        isInitialized = true

        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        // Se o SharedPreferences estiver vazio (ex: após desinstalação e reinstalação),
        // restaura automaticamente do Vault permanente.
        val hasExistingData = prefs.all.isNotEmpty() && prefs.contains("vault_synced_at")
        if (!hasExistingData) {
            val restored = restoreFromVault(context)
            if (restored) {
                Handler(Looper.getMainLooper()).post {
                    Toast.makeText(context, "✓ Perfil e credenciais restaurados automaticamente!", Toast.LENGTH_LONG).show()
                }
            }
        }

        // Listener ativo: toda alteração salva em SharedPreferences sincroniza com o Vault externo
        prefs.registerOnSharedPreferenceChangeListener { _, _ ->
            if (!isRestoring) {
                syncPrefsToVault(context)
            }
        }
    }

    /**
     * Retorna a lista de pastas candidatas onde o arquivo de Vault persistente pode residir.
     */
    private fun getVaultCandidateDirs(context: Context): List<File> {
        val dirs = mutableListOf<File>()
        try {
            val docs = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
            dirs.add(File(docs, VAULT_DIR_NAME))
        } catch (_: Exception) {}

        try {
            val ext = Environment.getExternalStorageDirectory()
            dirs.add(File(ext, "Documents/$VAULT_DIR_NAME"))
        } catch (_: Exception) {}

        try {
            val appExt = context.getExternalFilesDir(null)
            if (appExt != null) {
                dirs.add(File(appExt, ".vault"))
            }
        } catch (_: Exception) {}

        return dirs
    }

    /**
     * Salva uma credencial individual (login, senha, token, api key)
     */
    fun saveCredential(context: Context, key: String, value: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString("cred_$key", value).apply()
        syncPrefsToVault(context)
    }

    /**
     * Recupera uma credencial salva
     */
    fun getCredential(context: Context, key: String, defaultVal: String = ""): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString("cred_$key", defaultVal) ?: defaultVal
    }

    /**
     * Salva um pacote completo de credenciais e informações do usuário em JSON
     */
    fun saveUserAccount(context: Context, username: String, email: String, token: String, extraInfoJson: String? = null) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().apply {
            putString("cred_user_username", username)
            putString("cred_user_email", email)
            putString("cred_user_token", token)
            if (extraInfoJson != null) {
                putString("cred_user_extra", extraInfoJson)
            }
            apply()
        }
        syncPrefsToVault(context)
    }

    /**
     * Sincroniza todas as preferências e credenciais atuais para o arquivo de Vault criptografado
     */
    fun syncPrefsToVault(context: Context): Boolean {
        return try {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val allEntries = prefs.all
            if (allEntries.isEmpty()) return false

            val rootJson = JSONObject()
            val dataJson = JSONObject()

            for ((k, v) in allEntries) {
                if (k == "vault_synced_at") continue
                dataJson.put(k, v)
            }

            val timestamp = System.currentTimeMillis()
            rootJson.put("timestamp", timestamp)
            rootJson.put("version", 2)
            rootJson.put("app", "MontanhaMediaLab")
            rootJson.put("payload", dataJson)

            val plaintext = rootJson.toString()
            val encryptedBytes = encrypt(context, plaintext)

            var success = false
            for (dir in getVaultCandidateDirs(context)) {
                try {
                    if (!dir.exists()) {
                        dir.mkdirs()
                    }
                    val vaultFile = File(dir, VAULT_FILE_NAME)
                    FileOutputStream(vaultFile).use { fos ->
                        fos.write(encryptedBytes)
                        fos.flush()
                    }
                    success = true
                } catch (e: Exception) {
                    Log.w(TAG, "Tentativa de escrita em ${dir.absolutePath} falhou: ${e.message}")
                }
            }

            if (success) {
                prefs.edit().putLong("vault_synced_at", timestamp).apply()
            }
            success
        } catch (e: Exception) {
            Log.e(TAG, "Erro ao sincronizar Vault", e)
            false
        }
    }

    /**
     * Restaura preferências e credenciais a partir do arquivo persistente
     */
    fun restoreFromVault(context: Context): Boolean {
        for (dir in getVaultCandidateDirs(context)) {
            val vaultFile = File(dir, VAULT_FILE_NAME)
            if (vaultFile.exists() && vaultFile.length() > 0) {
                try {
                    val encryptedBytes = FileInputStream(vaultFile).use { it.readBytes() }
                    val decryptedText = decrypt(context, encryptedBytes) ?: continue
                    val rootJson = JSONObject(decryptedText)
                    val payload = rootJson.optJSONObject("payload") ?: continue

                    isRestoring = true
                    val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                    val editor = prefs.edit()

                    val keys = payload.keys()
                    while (keys.hasNext()) {
                        val key = keys.next()
                        when (val value = payload.get(key)) {
                            is Boolean -> editor.putBoolean(key, value)
                            is Int -> editor.putInt(key, value)
                            is Long -> editor.putLong(key, value)
                            is Double -> editor.putFloat(key, value.toFloat())
                            is String -> editor.putString(key, value)
                            else -> editor.putString(key, value.toString())
                        }
                    }

                    editor.putLong("vault_synced_at", rootJson.optLong("timestamp", System.currentTimeMillis()))
                    editor.apply()
                    isRestoring = false
                    Log.i(TAG, "Restauração do Vault concluída com sucesso a partir de ${vaultFile.absolutePath}")
                    return true
                } catch (e: Exception) {
                    isRestoring = false
                    Log.e(TAG, "Falha ao descriptografar vault em ${vaultFile.absolutePath}", e)
                }
            }
        }
        return false
    }

    /**
     * Deriva uma chave AES de 256 bits única e determinística vinculada ao hardware do telefone
     */
    private fun getDeviceSecretKey(context: Context): SecretKeySpec {
        val androidId = try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "DefaultAndroidId"
        } catch (_: Exception) {
            "FallbackId"
        }
        val seed = "$androidId:$INTERNAL_SALT:${context.packageName}"
        val sha256 = MessageDigest.getInstance("SHA-256")
        val keyBytes = sha256.digest(seed.toByteArray(Charsets.UTF_8))
        return SecretKeySpec(keyBytes, "AES")
    }

    private fun encrypt(context: Context, text: String): ByteArray {
        val keySpec = getDeviceSecretKey(context)
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        cipher.init(Cipher.ENCRYPT_MODE, keySpec)
        val iv = cipher.iv
        val ciphertext = cipher.doFinal(text.toByteArray(Charsets.UTF_8))

        // Formato binário: [16 bytes IV] + [ciphertext]
        val result = ByteArray(iv.size + ciphertext.size)
        System.arraycopy(iv, 0, result, 0, iv.size)
        System.arraycopy(ciphertext, 0, result, iv.size, ciphertext.size)
        return result
    }

    private fun decrypt(context: Context, data: ByteArray): String? {
        if (data.size <= 16) return null
        return try {
            val keySpec = getDeviceSecretKey(context)
            val iv = ByteArray(16)
            val ciphertext = ByteArray(data.size - 16)
            System.arraycopy(data, 0, iv, 0, 16)
            System.arraycopy(data, 16, ciphertext, 0, ciphertext.size)

            val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
            cipher.init(Cipher.DECRYPT_MODE, keySpec, IvParameterSpec(iv))
            val decryptedBytes = cipher.doFinal(ciphertext)
            String(decryptedBytes, Charsets.UTF_8)
        } catch (e: Exception) {
            Log.e(TAG, "Erro na descriptografia do vault", e)
            null
        }
    }
}
