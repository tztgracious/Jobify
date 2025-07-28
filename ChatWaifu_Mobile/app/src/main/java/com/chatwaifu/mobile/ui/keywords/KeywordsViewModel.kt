package com.chatwaifu.mobile.ui.keywords

import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.TargetJobRequest
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody

class KeywordsViewModel : ViewModel() {
    
    private val TAG = "KeywordsViewModel"
    
    val keywords = MutableLiveData<List<String>>()
    val isLoading = MutableLiveData<Boolean>()
    val error = MutableLiveData<String>()
    val targetJobSaved = MutableLiveData<Boolean>()
    
    private val apiService = JobifyApiService.create()
    
    fun loadKeywords(docId: String) {
        isLoading.value = true
        error.value = ""
        
        viewModelScope.launch {
            try {
                Log.d(TAG, "Starting keywords extraction for doc_id: $docId")
                
                // 轮询检查处理状态，最多等待60秒
                var attempts = 0
                val maxAttempts = 12 // 12次 * 5秒 = 60秒
                
                while (attempts < maxAttempts) {
                    attempts++
                    Log.d(TAG, "Checking keywords (attempt $attempts/$maxAttempts)")
                    
                    val docIdBody = RequestBody.create("text/plain".toMediaTypeOrNull(), docId)
                    val response = apiService.getKeywords(docIdBody)
                    
                    if (response.isSuccessful) {
                        val keywordsResponse = response.body()
                        Log.d(TAG, "Keywords response (attempt $attempts): $keywordsResponse")
                        
                        if (keywordsResponse?.finished == true) {
                            Log.d(TAG, "Keywords extracted successfully: ${keywordsResponse.keywords}")
                            keywords.postValue(keywordsResponse.keywords)
                            break // 处理完成，退出循环
                        } else {
                            // 还在处理中，等待5秒后重试
                            if (attempts < maxAttempts) {
                                Log.d(TAG, "Keywords still processing, waiting 5 seconds... (attempt $attempts/$maxAttempts)")
                                // 更新加载状态，显示处理进度
                                error.postValue("Extracting keywords... Please wait (${attempts}/${maxAttempts})")
                                kotlinx.coroutines.delay(5000) // 等待5秒
                            } else {
                                error.postValue("Keywords extraction is taking longer than expected. Please try again later.")
                            }
                        }
                    } else {
                        val errorBody = response.errorBody()?.string()
                        Log.e(TAG, "Keywords extraction failed with status: ${response.code()}, error: $errorBody")
                        error.postValue("Extraction failed: ${response.code()} - $errorBody")
                        break
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error extracting keywords", e)
                error.postValue("Network error: ${e.message}")
            } finally {
                isLoading.postValue(false)
            }
        }
    }
    
    fun saveTargetJob(docId: String, jobTitle: String, answerType: String = "text", onComplete: (Boolean) -> Unit) {
        isLoading.value = true
        error.value = ""
        
        viewModelScope.launch {
            try {
                Log.d(TAG, "Saving target job: $jobTitle for doc_id: $docId")
                
                val request = TargetJobRequest(
                    id = docId,
                    title = jobTitle,
                    answer_type = answerType
                )
                
                val response = apiService.saveTargetJob(request)
                
                if (response.isSuccessful) {
                    val targetJobResponse = response.body()
                    Log.d(TAG, "Target job saved successfully: $targetJobResponse")
                    targetJobSaved.postValue(true)
                    onComplete(true)
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Target job save failed with status: ${response.code()}, error: $errorBody")
                    error.postValue("Failed to save target job: ${response.code()} - $errorBody")
                    targetJobSaved.postValue(false)
                    onComplete(false)
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error saving target job", e)
                error.postValue("Network error: ${e.message}")
                targetJobSaved.postValue(false)
                onComplete(false)
            } finally {
                isLoading.postValue(false)
            }
        }
    }
    
    fun retryLoadKeywords(docId: String) {
        loadKeywords(docId)
    }
} 