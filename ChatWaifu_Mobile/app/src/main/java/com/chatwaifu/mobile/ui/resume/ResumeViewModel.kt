package com.chatwaifu.mobile.ui.resume

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response

class ResumeViewModel : ViewModel() {
    
    private val TAG = "ResumeViewModel"
    
    val uploadResult = MutableLiveData<UploadResult>()
    val isLoading = MutableLiveData<Boolean>()
    
    private val apiService = JobifyApiService.create()
    
    sealed class UploadResult {
        data class Success(val docId: String) : UploadResult()
        data class Error(val message: String) : UploadResult()
    }
    
    fun uploadResume(context: Context, uri: Uri) {
        isLoading.value = true
        
        viewModelScope.launch {
            try {
                // TODO: 实现真正的API调用
                /*
                val file = createMultipartBody(context, uri)
                val response = apiService.uploadResume(file)
                
                if (response.isSuccessful) {
                    val uploadResponse = response.body()
                    if (uploadResponse?.valid_file == true) {
                        uploadResponse.doc_id?.let { docId ->
                            Log.d(TAG, "Resume uploaded successfully, doc_id: $docId")
                            uploadResult.postValue(UploadResult.Success(docId))
                        } ?: run {
                            Log.e(TAG, "Upload successful but doc_id is null")
                            uploadResult.postValue(UploadResult.Error("Upload failed: no document ID"))
                        }
                    } else {
                        val errorMsg = uploadResponse?.error_msg ?: "Invalid file"
                        Log.e(TAG, "Upload failed: $errorMsg")
                        uploadResult.postValue(UploadResult.Error(errorMsg))
                    }
                } else {
                    Log.e(TAG, "Upload failed with status: ${response.code()}")
                    uploadResult.postValue(UploadResult.Error("Upload failed: ${response.code()}"))
                }
                */
                
                // 模拟API调用 - 暂时使用模拟数据
                Log.d(TAG, "Using mock data for resume upload")
                kotlinx.coroutines.delay(2000) // 模拟网络延迟
                uploadResult.postValue(UploadResult.Success("mock-doc-id-12345"))
                
            } catch (e: Exception) {
                Log.e(TAG, "Error uploading resume", e)
                uploadResult.postValue(UploadResult.Error("Network error: ${e.message}"))
            } finally {
                isLoading.postValue(false)
            }
        }
    }
    
    // TODO: 实现创建MultipartBody的辅助方法
    /*
    private fun createMultipartBody(context: Context, uri: Uri): MultipartBody.Part {
        val inputStream = context.contentResolver.openInputStream(uri)
        val fileBytes = inputStream?.readBytes() ?: ByteArray(0)
        inputStream?.close()
        
        val fileName = getFileName(context, uri) ?: "resume.pdf"
        val requestBody = RequestBody.create("application/pdf".toMediaTypeOrNull(), fileBytes)
        
        return MultipartBody.Part.createFormData("file", fileName, requestBody)
    }
    
    private fun getFileName(context: Context, uri: Uri): String? {
        return when (uri.scheme) {
            "content" -> {
                val cursor = context.contentResolver.query(uri, null, null, null, null)
                cursor?.use {
                    if (it.moveToFirst()) {
                        val displayNameIndex = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                        if (displayNameIndex != -1) {
                            return it.getString(displayNameIndex)
                        }
                    }
                }
                null
            }
            "file" -> uri.lastPathSegment
            else -> null
        }
    }
    */
} 