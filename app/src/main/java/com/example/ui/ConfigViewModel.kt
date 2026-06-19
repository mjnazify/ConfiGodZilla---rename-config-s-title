package com.example.ui

import android.app.Application
import android.util.Base64
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.ConfigDatabase
import com.example.data.ConfigHistory
import com.example.data.HistoryRepository
import com.example.engine.ConfigEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.nio.charset.StandardCharsets

sealed interface ProcessStatus {
    object Idle : ProcessStatus
    object Loading : ProcessStatus
    data class Success(val message: String) : ProcessStatus
    data class Error(val message: String) : ProcessStatus
}

class ConfigViewModel(application: Application) : AndroidViewModel(application) {

    private val repository: HistoryRepository
    val historyList: StateFlow<List<ConfigHistory>>

    init {
        val database = ConfigDatabase.getDatabase(application)
        repository = HistoryRepository(database.configHistoryDao())
        historyList = repository.allHistory.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )
    }

    // Input States
    private val _inputText = MutableStateFlow("")
    val inputText = _inputText.asStateFlow()

    private val _customName = MutableStateFlow("")
    val customName = _customName.asStateFlow()

    private val _enableReplacement = MutableStateFlow(false)
    val enableReplacement = _enableReplacement.asStateFlow()

    private val _findKeyword = MutableStateFlow("")
    val findKeyword = _findKeyword.asStateFlow()

    private val _replaceKeyword = MutableStateFlow("")
    val replaceKeyword = _replaceKeyword.asStateFlow()

    private val _outputFormat = MutableStateFlow("subscription") // "subscription" or "txt"
    val outputFormat = _outputFormat.asStateFlow()

    // Output States
    private val _resultText = MutableStateFlow("")
    val resultText = _resultText.asStateFlow()

    private val _status = MutableStateFlow<ProcessStatus>(ProcessStatus.Idle)
    val status = _status.asStateFlow()

    private val client = OkHttpClient()

    fun updateInputText(text: String) { _inputText.value = text }
    fun updateCustomName(name: String) { _customName.value = name }
    fun updateEnableReplacement(enable: Boolean) { _enableReplacement.value = enable }
    fun updateFindKeyword(keyword: String) { _findKeyword.value = keyword }
    fun updateReplaceKeyword(replace: String) { _replaceKeyword.value = replace }
    fun updateOutputFormat(format: String) { _outputFormat.value = format }
    fun updateResultText(text: String) { _resultText.value = text }
    fun resetStatus() { _status.value = ProcessStatus.Idle }

    fun setInputsFromHistory(history: ConfigHistory) {
        _inputText.value = history.rawConfigs
        if (history.outputMode == "subscription") {
            _outputFormat.value = "subscription"
        } else {
            _outputFormat.value = "txt"
        }
        _resultText.value = history.outputLinkOrPath
    }

    fun processConfigs(onSaveTextFile: ((String, String) -> Unit)?) {
        val input = _inputText.value.trim()
        val baseName = _customName.value.trim()
        val doReplace = _enableReplacement.value
        val kwFind = _findKeyword.value.trim()
        val kwReplace = _replaceKeyword.value.trim()
        val outMode = _outputFormat.value

        if (input.isEmpty()) {
            _status.value = ProcessStatus.Error("Please enter a subscription URL or paste config lines.")
            return
        }
        if (!doReplace && baseName.isEmpty()) {
            _status.value = ProcessStatus.Error("Please enter a custom config name.")
            return
        }
        if (doReplace && kwFind.isEmpty()) {
            _status.value = ProcessStatus.Error("Please enter the keyword to find.")
            return
        }

        viewModelScope.launch {
            _status.value = ProcessStatus.Loading
            try {
                val rawConfigsText = withContext(Dispatchers.IO) {
                    if (input.startsWith("http://", ignoreCase = true) || input.startsWith("https://", ignoreCase = true)) {
                        // Fetching subscription URL
                        val request = Request.Builder().url(input).get().build()
                        client.newCall(request).execute().use { response ->
                            if (!response.isSuccessful) {
                                throw Exception("Fetch URL failed with code: ${response.code}")
                            }
                            response.body?.string()?.trim() ?: throw Exception("Empty subscription response")
                        }
                    } else {
                        input
                    }
                }

                val configs = ConfigEngine.decodeSubscription(rawConfigsText)
                if (configs.isEmpty()) {
                    _status.value = ProcessStatus.Error("No valid configuration links found in input.")
                    return@launch
                }

                val renamed = configs.mapIndexed { index, cfg ->
                    ConfigEngine.renameConfig(
                        config = cfg,
                        baseName = if (!doReplace) baseName else "",
                        index = index + 1,
                        replaceKeyword = if (doReplace) kwFind else "",
                        replaceWith = if (doReplace) kwReplace else ""
                    )
                }

                val processedText = renamed.joinToString("\n")

                if (outMode == "subscription") {
                    // Upload to paste.rs
                    val encoded = Base64.encodeToString(
                        processedText.toByteArray(StandardCharsets.UTF_8),
                        Base64.NO_WRAP
                    )
                    
                    val link = withContext(Dispatchers.IO) {
                        val mediaType = "text/plain; charset=utf-8".toMediaType()
                        val requestBody = encoded.toRequestBody(mediaType)
                        val request = Request.Builder()
                            .url("https://paste.rs/")
                            .post(requestBody)
                            .build()

                        client.newCall(request).execute().use { response ->
                            if (!response.isSuccessful) {
                                throw Exception("paste.rs upload failed with code: ${response.code}")
                            }
                            response.body?.string()?.trim() ?: throw Exception("Empty response from paste.rs")
                        }
                    }

                    _resultText.value = link
                    _status.value = ProcessStatus.Success("DONE! COPY THE SUBSCRIPTION URL BELOW")

                    // Save to Room DB
                    repository.insertHistory(
                        ConfigHistory(
                            inputSummary = if (input.startsWith("http")) input else "$configs config lines pasted",
                            configCount = configs.size,
                            outputMode = "subscription",
                            outputLinkOrPath = link,
                            rawConfigs = input,
                            processedConfigs = processedText
                        )
                    )
                } else if (outMode == "txt") {
                    _resultText.value = processedText
                    _status.value = ProcessStatus.Success("DONE! COPY THE GENERATED OUTPUT BELOW")

                    if (onSaveTextFile != null) {
                        val initialName = if (!doReplace) "${baseName}_configs.txt" else "configs.txt"
                        onSaveTextFile(initialName, processedText)
                    }

                    // Save to Room DB
                    repository.insertHistory(
                        ConfigHistory(
                            inputSummary = if (input.startsWith("http")) input else "$configs config lines pasted",
                            configCount = configs.size,
                            outputMode = "txt",
                            outputLinkOrPath = "TXT File Exported",
                            rawConfigs = input,
                            processedConfigs = processedText
                        )
                    )
                }

            } catch (e: Exception) {
                _status.value = ProcessStatus.Error(e.localizedMessage ?: "Operation failed ❌")
            }
        }
    }

    fun deleteHistory(id: Int) {
        viewModelScope.launch {
            repository.deleteHistoryById(id)
        }
    }

    fun clearAllHistory() {
        viewModelScope.launch {
            repository.clearHistory()
        }
    }
}
