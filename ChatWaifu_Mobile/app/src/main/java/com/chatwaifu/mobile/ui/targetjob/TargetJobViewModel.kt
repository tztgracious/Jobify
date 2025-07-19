package com.chatwaifu.mobile.ui.targetjob

import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.TargetJobRequest
import kotlinx.coroutines.launch
import retrofit2.Response

class TargetJobViewModel : ViewModel() {
    
    private val TAG = "TargetJobViewModel"
    
    val saveResult = MutableLiveData<Boolean>()
    val isLoading = MutableLiveData<Boolean>()
    
    private val apiService = JobifyApiService.create()
    
    fun saveTargetJob(docId: String, title: String, location: String, salaryRange: String, tags: List<String>) {
        isLoading.value = true
        
        viewModelScope.launch {
            try {
                // TODO: 实现真正的API调用
                /*
                val request = TargetJobRequest(
                    doc_id = docId,  // 需要更新数据模型以包含doc_id
                    title = title,
                    location = location,
                    salary_range = salaryRange,
                    tags = tags
                )
                
                val response = apiService.saveTargetJob(request)
                
                if (response.isSuccessful) {
                    Log.d(TAG, "Target job saved successfully")
                    saveResult.postValue(true)
                } else {
                    Log.e(TAG, "Failed to save target job: ${response.code()}")
                    saveResult.postValue(false)
                }
                */
                
                // 模拟API调用 - 暂时使用模拟数据
                Log.d(TAG, "Using mock data for target job save, docId: $docId")
                Log.d(TAG, "Mock data - Title: $title, Location: $location, Salary: $salaryRange, Tags: $tags")
                kotlinx.coroutines.delay(1000) // 模拟网络延迟
                Log.d(TAG, "Target job saved successfully (mock)")
                saveResult.postValue(true)
                
            } catch (e: Exception) {
                Log.e(TAG, "Error saving target job", e)
                saveResult.postValue(false)
            } finally {
                isLoading.postValue(false)
            }
        }
    }
} 