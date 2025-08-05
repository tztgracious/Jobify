package com.chatwaifu.mobile.data.network

import com.google.gson.annotations.SerializedName
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.security.cert.X509Certificate
import javax.net.ssl.*

interface JobifyApiService {
    
    @Multipart
    @POST("api/v1/upload-resume/")
    suspend fun uploadResume(
        @Part file: MultipartBody.Part
    ): Response<UploadResumeResponse>
    
    @Multipart
    @POST("api/v1/get-keywords/")
    suspend fun getKeywords(
        @Part("id") docId: RequestBody
    ): Response<KeywordsResponse>
    
    @POST("api/v1/get-grammar-results/")
    suspend fun getGrammarResults(
        @Body request: GrammarRequest
    ): Response<GrammarResponse>
    
    @POST("api/v1/target-job/")
    suspend fun saveTargetJob(
        @Body request: TargetJobRequest
    ): Response<TargetJobResponse>
    
    @POST("api/v1/get-all-questions/")
    suspend fun getAllQuestions(
        @Body request: QuestionsRequest
    ): Response<AllQuestionsResponse>
    
    @POST("api/v1/submit-tech-answer/")
    suspend fun submitTechAnswer(
        @Body request: TechAnswerRequest
    ): Response<TechAnswerResponse>

    // GraphRAG API endpoints
    @GET("search/global")
    suspend fun searchGlobal(
        @Query("query") query: String
    ): Response<GraphRAGResponse>

    @GET("search/local")
    suspend fun searchLocal(
        @Query("query") query: String
    ): Response<GraphRAGResponse>

    @GET("search/basic")
    suspend fun searchBasic(
        @Query("query") query: String
    ): Response<GraphRAGResponse>

    @GET("search/drift")
    suspend fun searchDrift(
        @Query("query") query: String
    ): Response<GraphRAGResponse>

    // 提交面试答案 - 支持文本和视频（严格按照API文档格式）
    @POST("api/v1/submit-interview-answer/")
    suspend fun submitInterviewAnswerText(
        @Body request: SubmitInterviewAnswerRequest
    ): Response<SubmitAnswerResponse>
    
    @Multipart
    @POST("api/v1/submit-interview-answer/")
    suspend fun submitInterviewAnswerVideo(
        @Part("id") id: RequestBody,
        @Part("index") index: RequestBody,
        @Part("answer_type") answerType: RequestBody,
        @Part("question") question: RequestBody,
        @Part video: MultipartBody.Part
    ): Response<SubmitAnswerResponse>
    
    // 获取面试反馈
    @POST("api/v1/feedback/")
    suspend fun getFeedback(
        @Body request: FeedbackRequest
    ): Response<FeedbackResponse>
    
    // 清理简历数据
    @POST("api/v1/remove-resume/")
    suspend fun removeResume(
        @Body request: RemoveResumeRequest
    ): Response<RemoveResumeResponse>
    
    // 上传文件更新数据库
    @Multipart
    @POST("api/v1/upload-resume/")
    suspend fun uploadResumeForUpdate(
        @Part file: MultipartBody.Part
    ): Response<UploadResumeResponse>
    
    companion object {
        private const val BASE_URL = "https://115.29.170.231/"
        private const val GRAPHRAG_BASE_URL = "https://115.29.170.231/ai/"  // 使用正确的HTTPS路径
        
        fun create(): JobifyApiService {
            val loggingInterceptor = okhttp3.logging.HttpLoggingInterceptor().apply {
                level = okhttp3.logging.HttpLoggingInterceptor.Level.BODY
            }
            
            // 创建信任所有证书的SSL上下文（仅用于开发环境）
            val trustAllCerts = arrayOf<TrustManager>(object : X509TrustManager {
                override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
            })
            
            val sslContext = SSLContext.getInstance("SSL")
            sslContext.init(null, trustAllCerts, java.security.SecureRandom())
            
            val client = okhttp3.OkHttpClient.Builder()
                .addInterceptor(loggingInterceptor)
                .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .sslSocketFactory(sslContext.socketFactory, trustAllCerts[0] as X509TrustManager)
                .hostnameVerifier { _, _ -> true }  // 信任所有主机名
                .build()
            
            return Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(JobifyApiService::class.java)
        }
        
        fun createGraphRAG(): JobifyApiService {
            val loggingInterceptor = okhttp3.logging.HttpLoggingInterceptor().apply {
                level = okhttp3.logging.HttpLoggingInterceptor.Level.BODY
            }
            
            // 创建信任所有证书的SSL上下文（仅用于开发环境）
            val trustAllCerts = arrayOf<TrustManager>(object : X509TrustManager {
                override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
            })
            
            val sslContext = SSLContext.getInstance("SSL")
            sslContext.init(null, trustAllCerts, java.security.SecureRandom())
            
            val client = okhttp3.OkHttpClient.Builder()
                .addInterceptor(loggingInterceptor)
                .connectTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
                .writeTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
                .sslSocketFactory(sslContext.socketFactory, trustAllCerts[0] as X509TrustManager)
                .hostnameVerifier { _, _ -> true }  // 信任所有主机名
                .retryOnConnectionFailure(true)
                .build()
            
            return Retrofit.Builder()
                .baseUrl(GRAPHRAG_BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(JobifyApiService::class.java)
        }
    }
}

// 数据模型
data class UploadResumeResponse(
    val id: String?,
    val valid_file: Boolean,
    val error_msg: String?
)

data class KeywordsResponse(
    val finished: Boolean,
    val keywords: List<String>,
    val error: String
)

data class GrammarRequest(
    val id: String
)

data class GrammarResponse(
    val finished: Boolean,
    val grammar_check: GrammarCheck?,
    val error: String
)

data class GrammarCheck(
    val language: GrammarLanguage,
    val matches: List<GrammarMatch>
)

data class GrammarLanguage(
    val code: String,
    val name: String,
    val detectedLanguage: GrammarDetectedLanguage
)

data class GrammarDetectedLanguage(
    val code: String,
    val name: String,
    val source: String,
    val confidence: Double
)

data class GrammarMatch(
    val message: String,
    val shortMessage: String?,
    val offset: Int,
    val length: Int,
    val replacements: List<GrammarReplacement>,
    val context: GrammarContext,
    val sentence: String,
    val rule: GrammarRule
)

data class GrammarReplacement(
    val value: String
)

data class GrammarContext(
    val text: String,
    val offset: Int,
    val length: Int
)

data class GrammarRule(
    val id: String,
    val category: GrammarCategory
)

data class GrammarCategory(
    val id: String,
    val name: String
)

data class TargetJobRequest(
    val id: String,  // 根据API文档，应该是id而不是doc_id
    val title: String,
    val answer_type: String = "text"  // 默认文本模式
)

data class TargetJobResponse(
    val id: String,
    val message: String,
    val answer_type: String
)

data class QuestionsRequest(
    val id: String
)

data class AllQuestionsResponse(
    val id: String,
    val finished: Boolean,
    val tech_questions: List<String>,
    val interview_questions: List<String>,
    val message: String
)

data class TechAnswerRequest(
    @SerializedName("id")
    val id: String,
    @SerializedName("index")
    val index: Int,
    @SerializedName("question")
    val question: String,
    @SerializedName("answer")
    val answer: String
)

data class TechAnswerResponse(
    val id: String,
    val message: String,
    val index: Int,
    val question: String,
    val answer: String
)

// GraphRAG API响应数据模型
data class GraphRAGResponse(
    val response: String,
    val context_data: Any? = null
)

// 提交面试答案请求数据（文本格式）
data class SubmitInterviewAnswerRequest(
    val id: String,
    val index: Int,
    val answer_type: String,
    val question: String,
    val answer: String
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

// 反馈请求数据模型
data class FeedbackRequest(
    val id: String,
    val answer_type: String = "text"
)

// 反馈响应数据模型
data class FeedbackResponse(
    val id: String,
    val feedbacks: Map<String, String>?,
    val completed: Boolean?,
    val message: String?,
    val duration: String?
)

// 清理简历请求数据模型
data class RemoveResumeRequest(
    val id: String
)

// 清理简历响应数据模型
data class RemoveResumeResponse(
    val message: String
) 