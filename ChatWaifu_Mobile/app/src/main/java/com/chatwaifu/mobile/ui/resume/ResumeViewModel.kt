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
                Log.d(TAG, "Starting real API call for resume upload")
                Log.d(TAG, "File URI: $uri")
                
                val file = createMultipartBody(context, uri)
                Log.d(TAG, "MultipartBody created successfully")
                
                val response = apiService.uploadResume(file)
                Log.d(TAG, "API call completed, status code: ${response.code()}")
                
                if (response.isSuccessful) {
                    val uploadResponse = response.body()
                    Log.d(TAG, "Upload response: $uploadResponse")
                    
                    if (uploadResponse?.valid_file == true) {
                        uploadResponse.id?.let { docId ->
                            Log.d(TAG, "Resume uploaded successfully, doc_id: $docId")
                            uploadResult.postValue(UploadResult.Success(docId))
                        } ?: run {
                            Log.e(TAG, "Upload successful but id is null")
                            uploadResult.postValue(UploadResult.Error("Upload failed: no document ID"))
                        }
                    } else {
                        val errorMsg = uploadResponse?.error_msg ?: "Invalid file"
                        Log.e(TAG, "Upload failed: $errorMsg")
                        uploadResult.postValue(UploadResult.Error(errorMsg))
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Upload failed with status: ${response.code()}, error: $errorBody")
                    uploadResult.postValue(UploadResult.Error("Upload failed: ${response.code()} - $errorBody"))
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error uploading resume", e)
                uploadResult.postValue(UploadResult.Error("Network error: ${e.message}"))
            } finally {
                isLoading.postValue(false)
            }
        }
    }
    
    private fun createMultipartBody(context: Context, uri: Uri): MultipartBody.Part {
        val inputStream = context.contentResolver.openInputStream(uri)
        val fileBytes = inputStream?.readBytes() ?: ByteArray(0)
        inputStream?.close()
        
        val fileName = getFileName(context, uri) ?: "resume.pdf"
        Log.d(TAG, "File name: $fileName, File size: ${fileBytes.size} bytes")
        
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
} 