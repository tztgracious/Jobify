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
    
    companion object {
        private const val BASE_URL = "http://localhost:8000/"
        
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