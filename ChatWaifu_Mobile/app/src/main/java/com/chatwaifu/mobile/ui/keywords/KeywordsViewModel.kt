package com.chatwaifu.mobile.ui.keywords

import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody

class KeywordsViewModel : ViewModel() {
    
    private val TAG = "KeywordsViewModel"
    
    val keywords = MutableLiveData<List<String>>()
    val isLoading = MutableLiveData<Boolean>()
    val error = MutableLiveData<String>()
    
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
    
    fun retryLoadKeywords(docId: String) {
        loadKeywords(docId)
    }
} 