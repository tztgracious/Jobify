package com.chatwaifu.mobile.data.network

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

interface JobifyApiService {
    
    @Multipart
    @POST("api/v1/upload-resume/")
    suspend fun uploadResume(
        @Part file: MultipartBody.Part
    ): Response<UploadResumeResponse>
    
    @Multipart
    @POST("api/v1/get-keywords/")
    suspend fun getKeywords(
        @Part("doc_id") docId: RequestBody
    ): Response<KeywordsResponse>
    
    @POST("api/v1/target-job/")
    suspend fun saveTargetJob(
        @Body request: TargetJobRequest
    ): Response<TargetJobResponse>
    
    @POST("api/v1/get-questions/")
    suspend fun getInterviewQuestions(
        @Body request: QuestionsRequest
    ): Response<QuestionsResponse>

    // 提交面试答案 - 支持文本和视频（严格按照API文档格式）
    @Multipart
    @POST("api/v1/submit-interview-answer/")
    suspend fun submitInterviewAnswer(
        @Part("id") id: RequestBody,
        @Part("index") index: RequestBody,
        @Part("answer_type") answerType: RequestBody,
        @Part("question") question: RequestBody,
        @Part video: MultipartBody.Part? = null,
        @Part("answer") textAnswer: RequestBody? = null
    ): Response<SubmitAnswerResponse>
    
    companion object {
        private const val BASE_URL = "http://10.0.2.2:8000/"  // 使用Android模拟器的localhost映射
        
        fun create(): JobifyApiService {
            return Retrofit.Builder()
                .baseUrl(BASE_URL)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(JobifyApiService::class.java)
        }
    }
}

// 数据模型
data class UploadResumeResponse(
    val doc_id: String?,
    val valid_file: Boolean,
    val error_msg: String?
)

data class KeywordsResponse(
    val finished: Boolean,
    val keywords: List<String>,
    val error: String
)

data class TargetJobRequest(
    val doc_id: String,  // 添加doc_id字段以符合API文档
    val title: String,
    val location: String,
    val salary_range: String,
    val tags: List<String>
)

data class TargetJobResponse(
    val message: String
)

data class QuestionsRequest(
    val doc_id: String
)

data class QuestionsResponse(
    val finished: Boolean,
    val questions: List<String>,
    val error: String
)

// 提交答案响应数据（按照API文档格式）
data class SubmitAnswerResponse(
    val id: String,
    val message: String,
    val question: String,
    val answer_type: String,
    val answer: String? = null,           // 文本答案
    val video_path: String? = null,       // 视频路径
    val video_filename: String? = null,   // 视频文件名
    val video_size: Long? = null,         // 视频文件大小
    val progress: Double,                 // 进度百分比
    val is_completed: Boolean             // 是否完成
) 