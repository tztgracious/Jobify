package com.chatwaifu.mobile.data.network

import android.content.Context
import android.net.Uri
import android.util.Log
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import com.chatwaifu.mobile.data.network.SubmitInterviewAnswerRequest

class VideoUploadService(private val context: Context) {
    
    companion object {
        private const val TAG = "VideoUploadService"
    }
    
    private val apiService = JobifyApiService.create()
    
    /**
     * 上传视频答案
     * @param id 用户ID/会话ID
     * @param questionIndex 问题索引
     * @param question 问题内容
     * @param videoFile 视频文件
     * @param callback 上传结果回调
     */
    suspend fun uploadVideoAnswer(
        id: String,
        questionIndex: Int,
        question: String,
        videoFile: File,
        onSuccess: (SubmitAnswerResponse) -> Unit,
        onError: (String) -> Unit
    ) {
        try {
            Log.d(TAG, "开始上传视频答案 - ID: $id, 问题索引: $questionIndex")
            
            // 按照API文档格式创建请求参数
            val idBody = id.toRequestBody("text/plain".toMediaTypeOrNull())
            val indexBody = questionIndex.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val answerTypeBody = "video".toRequestBody("text/plain".toMediaTypeOrNull())
            val questionBody = question.toRequestBody("text/plain".toMediaTypeOrNull())
            
            // 创建视频文件的MultipartBody
            val requestFile = videoFile.asRequestBody("video/mp4".toMediaTypeOrNull())
            val videoPart = MultipartBody.Part.createFormData("video", videoFile.name, requestFile)
            
            Log.d(TAG, "发送API请求 - 文件大小: ${videoFile.length()} bytes")
            
            val response = apiService.submitInterviewAnswerVideo(
                id = idBody,
                index = indexBody,
                answerType = answerTypeBody,
                question = questionBody,
                video = videoPart
            )
            
            if (response.isSuccessful) {
                val result = response.body()
                if (result != null) {
                    Log.d(TAG, "视频上传成功: ${result.message}")
                    onSuccess(result)
                } else {
                    Log.e(TAG, "上传成功但响应为空")
                    onError("上传成功但服务器响应为空")
                }
            } else {
                val errorMsg = "上传失败: HTTP ${response.code()}"
                Log.e(TAG, errorMsg)
                onError(errorMsg)
            }
            
        } catch (e: Exception) {
            val errorMsg = "网络错误: ${e.message}"
            Log.e(TAG, errorMsg, e)
            onError(errorMsg)
        }
    }
    
    /**
     * 上传文本答案
     * @param id 用户ID/会话ID
     * @param questionIndex 问题索引
     * @param question 问题内容
     * @param textAnswer 文本答案
     */
    suspend fun uploadTextAnswer(
        id: String,
        questionIndex: Int,
        question: String,
        textAnswer: String,
        onSuccess: (SubmitAnswerResponse) -> Unit,
        onError: (String) -> Unit
    ) {
        try {
            Log.d(TAG, "开始上传文本答案 - ID: $id, 问题索引: $questionIndex")
            
            // 使用JSON格式提交文本答案
            val request = SubmitInterviewAnswerRequest(
                id = id,
                index = questionIndex,
                answer_type = "text",
                question = question,
                answer = textAnswer
            )
            
            val response = apiService.submitInterviewAnswerText(request)
            
            if (response.isSuccessful) {
                val result = response.body()
                if (result != null) {
                    Log.d(TAG, "文本答案上传成功: ${result.message}")
                    onSuccess(result)
                } else {
                    onError("上传成功但服务器响应为空")
                }
            } else {
                val errorMsg = "上传失败: HTTP ${response.code()}"
                Log.e(TAG, errorMsg)
                onError(errorMsg)
            }
            
        } catch (e: Exception) {
            val errorMsg = "网络错误: ${e.message}"
            Log.e(TAG, errorMsg, e)
            onError(errorMsg)
        }
    }
} 