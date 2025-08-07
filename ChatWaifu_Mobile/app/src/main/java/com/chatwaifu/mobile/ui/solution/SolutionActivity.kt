package com.chatwaifu.mobile.ui.solution

import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.chatwaifu.mobile.databinding.ActivitySolutionBinding
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.FeedbackRequest
import com.chatwaifu.mobile.data.network.FeedbackResponse
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

class SolutionActivity : AppCompatActivity() {
    private lateinit var binding: ActivitySolutionBinding
    private val apiService = JobifyApiService.create()
    private val TAG = "SolutionActivity"
    private var isLoadingFeedback = false
    private var maxRetries = 12 // 最多重试12次 (12 * 10秒 = 2分钟)，之后用户可以上拉刷新
    private var currentRetry = 0
    private var docId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySolutionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 从intent获取传递的数据
        val questions = intent.getStringArrayListExtra("questions") ?: arrayListOf()
        val answers = intent.getStringArrayListExtra("answers") ?: arrayListOf()
        val solutions = intent.getStringArrayListExtra("solutions") ?: arrayListOf()
        docId = intent.getStringExtra("doc_id")

        // 填充UI
        if (questions.size >= 1) {
            binding.tvQuestion1.text = "Question 1: ${questions.getOrNull(0) ?: ""}"
            binding.tvYourAnswer1.text = "Your Answer: ${answers.getOrNull(0) ?: ""}"
            binding.tvStandardAnswer1.text = "Solution: ${solutions.getOrNull(0) ?: ""}"
        }
        
        if (questions.size >= 2) {
            binding.tvQuestion2.text = "Question 2: ${questions.getOrNull(1) ?: ""}"
            binding.tvYourAnswer2.text = "Your Answer: ${answers.getOrNull(1) ?: ""}"
            binding.tvStandardAnswer2.text = "Solution: ${solutions.getOrNull(1) ?: ""}"
        }
        
        if (questions.size >= 3) {
            binding.tvQuestion3.text = "Question 3: ${questions.getOrNull(2) ?: ""}"
            binding.tvYourAnswer3.text = "Your Answer: ${answers.getOrNull(2) ?: ""}"
            binding.tvStandardAnswer3.text = "Solution: ${solutions.getOrNull(2) ?: ""}"
        }

        // 设置上拉刷新
        binding.swipeRefresh.setOnRefreshListener {
            Log.d(TAG, "Pull-to-refresh triggered")
            refreshFeedback()
        }
        
        // 加载反馈
        docId?.let { id ->
            Log.d(TAG, "Loading feedback for doc_id: $id")
            loadFeedback(id)
        } ?: run {
            Log.e(TAG, "No doc_id provided for feedback loading")
            showFeedbackError("No document ID provided")
        }

        binding.btnBack.setOnClickListener { finish() }
        
        binding.btnNext.setOnClickListener {
            // 跳转到Tips页面
            val intent = android.content.Intent(this, com.chatwaifu.mobile.ui.tips.TipsActivity::class.java)
            intent.putExtra("doc_id", docId)
            startActivity(intent)
            finish()
        }
    }
    
    private fun refreshFeedback() {
        Log.d(TAG, "Refreshing feedback...")
        // 重置计数器并重新加载
        currentRetry = 0
        isLoadingFeedback = false
        
        docId?.let { id ->
            loadFeedback(id)
        } ?: run {
            Log.e(TAG, "No doc_id available for refresh")
            showFeedbackError("No document ID available")
            binding.swipeRefresh.isRefreshing = false
        }
    }
    
    private fun loadFeedback(docId: String) {
        if (isLoadingFeedback) {
            Log.d(TAG, "Already loading feedback, skipping duplicate request")
            return
        }
        
        isLoadingFeedback = true
        currentRetry++
        Log.d(TAG, "Loading feedback for doc_id: $docId (Attempt $currentRetry/$maxRetries)")
        
        lifecycleScope.launch {
            var feedbackCompleted = false
            
            try {
                // 显示加载状态
                showLoadingState(true, currentRetry, maxRetries)
                
                val request = FeedbackRequest(id = docId, answer_type = "text")
                val response = apiService.getFeedback(request)
                
                if (response.isSuccessful) {
                    val feedbackData = response.body()
                    Log.d(TAG, "Feedback response: $feedbackData")
                    
                    if (feedbackData != null) {
                        Log.d(TAG, "Response details - completed: ${feedbackData.completed}, message: ${feedbackData.message}")
                        
                        // 检查是否完成
                        if (feedbackData.completed == true && feedbackData.feedbacks != null && feedbackData.feedbacks.isNotEmpty()) {
                            Log.d(TAG, "Feedback completed successfully")
                            Log.d(TAG, "Feedbacks map: ${feedbackData.feedbacks}")
                            Log.d(TAG, "Feedbacks keys: ${feedbackData.feedbacks.keys}")
                            updateUIWithFeedback(feedbackData.feedbacks)
                            feedbackCompleted = true
                            isLoadingFeedback = false
                            showLoadingState(false, 0, 0)
                            return@launch
                        } else if (feedbackData.completed == false) {
                            // 反馈还在处理中，继续重试
                            Log.d(TAG, "Feedback still processing: ${feedbackData.message}")
                            if (currentRetry < maxRetries) {
                                delay(10000) // 等待10秒
                                isLoadingFeedback = false
                                loadFeedback(docId) // 递归重试
                                return@launch
                            } else {
                                Log.w(TAG, "Max retries reached, giving up")
                                showFeedbackError("AI feedback generation is taking longer than expected (>2 minutes). This may be due to high server load or complex analysis. Please try refreshing in a few minutes.")
                            }
                        } else {
                            Log.w(TAG, "Unexpected feedback state: completed=${feedbackData.completed}, feedbacks=${feedbackData.feedbacks}")
                            showFeedbackError("Unexpected feedback state. Please try again.")
                        }
                    } else {
                        Log.w(TAG, "Empty feedback response")
                        showFeedbackError("Empty response from server.")
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Failed to load feedback: ${response.code()}, error: $errorBody")
                    showFeedbackError("Failed to load feedback: ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error loading feedback", e)
                Log.e(TAG, "Exception type: ${e.javaClass.simpleName}")
                Log.e(TAG, "Exception message: ${e.message}")
                Log.e(TAG, "Exception stack trace: ${e.stackTraceToString()}")
                showFeedbackError("Network error: ${e.message}")
            } finally {
                isLoadingFeedback = false
                if (currentRetry >= maxRetries || feedbackCompleted) {
                    showLoadingState(false, 0, 0)
                }
            }
        }
    }
    
    private fun updateUIWithFeedback(feedbacks: Map<String, String>) {
        Log.d(TAG, "Updating UI with feedback: $feedbacks")
        
        // 调试：打印所有可用的字段
        Log.d(TAG, "Available feedback keys: ${feedbacks.keys}")
        
        // 更新每个问题的反馈
        feedbacks["question_1_feedback"]?.let { feedback ->
            binding.tvFeedback1?.text = "Feedback: $feedback"
            binding.tvFeedback1?.visibility = android.view.View.VISIBLE
        } ?: run {
            binding.tvFeedback1?.text = "Feedback: No feedback available for this question."
            binding.tvFeedback1?.visibility = android.view.View.VISIBLE
        }
        
        feedbacks["question_2_feedback"]?.let { feedback ->
            binding.tvFeedback2?.text = "Feedback: $feedback"
            binding.tvFeedback2?.visibility = android.view.View.VISIBLE
        } ?: run {
            binding.tvFeedback2?.text = "Feedback: No feedback available for this question."
            binding.tvFeedback2?.visibility = android.view.View.VISIBLE
        }
        
        feedbacks["question_3_feedback"]?.let { feedback ->
            binding.tvFeedback3?.text = "Feedback: $feedback"
            binding.tvFeedback3?.visibility = android.view.View.VISIBLE
        } ?: run {
            binding.tvFeedback3?.text = "Feedback: No feedback available for this question."
            binding.tvFeedback3?.visibility = android.view.View.VISIBLE
        }
        
        // 更新技术问题反馈
        feedbacks["tech_question_feedback"]?.let { feedback ->
            binding.tvTechFeedback?.text = "Tech Feedback: $feedback"
            binding.tvTechFeedback?.visibility = android.view.View.VISIBLE
        } ?: run {
            binding.tvTechFeedback?.text = "Tech Feedback: No technical feedback available."
            binding.tvTechFeedback?.visibility = android.view.View.VISIBLE
        }
        
        // 更新总结 - 尝试多个可能的字段名
        val summaryText = feedbacks["summary"] ?: feedbacks["overall_summary"] ?: feedbacks["interview_summary"] ?: feedbacks["final_summary"]
        summaryText?.let { summary ->
            binding.tvSummary?.text = summary
            binding.tvSummary?.visibility = android.view.View.VISIBLE
            // 显示成功提示
            Toast.makeText(this, "Interview feedback loaded successfully!", Toast.LENGTH_SHORT).show()
        } ?: run {
            binding.tvSummary?.text = "Interview completed. Review your answers and practice more to improve your performance."
            binding.tvSummary?.visibility = android.view.View.VISIBLE
        }
    }
    
    private fun showFeedbackError(errorMessage: String) {
        // 隐藏SwipeRefresh指示器
        binding.swipeRefresh.isRefreshing = false
        
        // 显示错误信息
        Log.e(TAG, errorMessage)
        Toast.makeText(this, errorMessage, Toast.LENGTH_SHORT).show()
        
        // 显示默认内容而不是隐藏卡片
        binding.tvFeedback1?.text = "Feedback: Unable to load feedback. Pull down to refresh."
        binding.tvFeedback1?.visibility = android.view.View.VISIBLE
        
        binding.tvFeedback2?.text = "Feedback: Unable to load feedback. Please try again later."
        binding.tvFeedback2?.visibility = android.view.View.VISIBLE
        
        binding.tvFeedback3?.text = "Feedback: Unable to load feedback. Pull down to refresh."
        binding.tvFeedback3?.visibility = android.view.View.VISIBLE
        
        binding.tvTechFeedback?.text = "Tech Feedback: Unable to load technical feedback."
        binding.tvTechFeedback?.visibility = android.view.View.VISIBLE
        
        binding.tvSummary?.text = "Interview completed. Review your answers and practice more to improve your performance."
        binding.tvSummary?.visibility = android.view.View.VISIBLE
    }

    private fun showLoadingState(show: Boolean, currentAttempt: Int = 0, maxAttempts: Int = 0) {
        if (show) {
            val message = if (currentAttempt > 0 && maxAttempts > 0) {
                "Loading feedback... (Attempt $currentAttempt/$maxAttempts)"
            } else {
                "Loading feedback..."
            }
            
            // 如果不是通过SwipeRefresh触发的，显示SwipeRefresh指示器
            if (!binding.swipeRefresh.isRefreshing) {
                binding.swipeRefresh.isRefreshing = true
            }
            
            // 显示在反馈区域
            binding.tvFeedback1?.text = message
            binding.tvFeedback1?.visibility = android.view.View.VISIBLE
            
            binding.tvFeedback2?.text = "Please wait, AI is generating personalized feedback..."
            binding.tvFeedback2?.visibility = android.view.View.VISIBLE
            
            binding.tvFeedback3?.text = "AI feedback generation may take 2-5 minutes. Pull down to refresh if needed."
            binding.tvFeedback3?.visibility = android.view.View.VISIBLE
            
            binding.tvTechFeedback?.text = "Tech Feedback: Processing..."
            binding.tvTechFeedback?.visibility = android.view.View.VISIBLE
            
            binding.tvSummary?.text = "Generating comprehensive interview analysis..."
            binding.tvSummary?.visibility = android.view.View.VISIBLE
            
            Log.d(TAG, message)
        } else {
            // 隐藏SwipeRefresh指示器
            binding.swipeRefresh.isRefreshing = false
            Log.d(TAG, "Loading completed")
        }
    }
} 