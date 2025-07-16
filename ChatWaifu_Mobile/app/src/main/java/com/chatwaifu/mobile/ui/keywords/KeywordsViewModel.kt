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
                // TODO: 实现真正的API调用
                /*
                val docIdBody = RequestBody.create("text/plain".toMediaTypeOrNull(), docId)
                val response = apiService.getKeywords(docIdBody)
                
                if (response.isSuccessful) {
                    val keywordsResponse = response.body()
                    if (keywordsResponse?.finished == true) {
                        Log.d(TAG, "Keywords loaded successfully: ${keywordsResponse.keywords}")
                        keywords.postValue(keywordsResponse.keywords)
                    } else {
                        Log.d(TAG, "Keywords still processing...")
                        error.postValue("Keywords still processing...")
                    }
                } else {
                    Log.e(TAG, "Failed to load keywords: ${response.code()}")
                    error.postValue("Failed to load keywords: ${response.code()}")
                }
                */
                
                // 模拟API调用 - 暂时使用模拟数据
                Log.d(TAG, "Using mock data for keywords, docId: $docId")
                kotlinx.coroutines.delay(1500) // 模拟网络延迟
                
                // 模拟不同的关键词结果
                val mockKeywords = when (docId) {
                    "mock-doc-id-12345" -> listOf("Java", "Kotlin", "Android", "REST API", "Retrofit", "MVVM", "Git", "SQLite")
                    "mock-doc-id-67890" -> listOf("Python", "Django", "Machine Learning", "TensorFlow", "Pandas", "NumPy", "Scikit-learn")
                    else -> listOf("JavaScript", "React", "Node.js", "TypeScript", "HTML", "CSS", "MongoDB", "Express")
                }
                
                keywords.postValue(mockKeywords)
                
            } catch (e: Exception) {
                Log.e(TAG, "Error loading keywords", e)
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