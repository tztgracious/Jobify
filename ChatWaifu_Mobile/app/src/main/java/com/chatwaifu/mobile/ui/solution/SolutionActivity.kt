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

class SolutionActivity : AppCompatActivity() {
    private lateinit var binding: ActivitySolutionBinding
    private val apiService = JobifyApiService.create()
    private val TAG = "SolutionActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySolutionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 从intent获取传递的数据
        val questions = intent.getStringArrayListExtra("questions") ?: arrayListOf()
        val answers = intent.getStringArrayListExtra("answers") ?: arrayListOf()
        val solutions = intent.getStringArrayListExtra("solutions") ?: arrayListOf()
        val docId = intent.getStringExtra("doc_id")

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

        // 加载反馈
        docId?.let { id ->
            loadFeedback(id)
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
    
    private fun loadFeedback(docId: String) {
        Log.d(TAG, "Loading feedback for doc_id: $docId")
        
        // 显示加载状态
        showLoadingState(true)
        
        lifecycleScope.launch {
            try {
                val request = FeedbackRequest(id = docId, answer_type = "text")
                val response = apiService.getFeedback(request)
                
                if (response.isSuccessful) {
                    val feedbackData = response.body()
                    Log.d(TAG, "Feedback response: $feedbackData")
                    Log.d(TAG, "Feedback data type: ${feedbackData?.javaClass?.simpleName}")
                    
                    if (feedbackData != null && feedbackData.feedbacks.isNotEmpty()) {
                        Log.d(TAG, "Feedbacks map: ${feedbackData.feedbacks}")
                        Log.d(TAG, "Feedbacks keys: ${feedbackData.feedbacks.keys}")
                        updateUIWithFeedback(feedbackData.feedbacks)
                    } else {
                        Log.w(TAG, "Empty feedback received")
                        showFeedbackError("No feedback available yet. Please try again later.")
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Failed to load feedback: ${response.code()}, error: $errorBody")
                    showFeedbackError("Failed to load feedback: ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error loading feedback", e)
                showFeedbackError("Network error: ${e.message}")
            } finally {
                // 隐藏加载状态
                showLoadingState(false)
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
        // 显示错误信息，可以添加一个TextView来显示错误
        Log.e(TAG, errorMessage)
        Toast.makeText(this, errorMessage, Toast.LENGTH_SHORT).show()
        
        // 显示默认内容而不是隐藏卡片
        binding.tvFeedback1?.text = "Feedback: Unable to load feedback. Please try again later."
        binding.tvFeedback1?.visibility = android.view.View.VISIBLE
        
        binding.tvFeedback2?.text = "Feedback: Unable to load feedback. Please try again later."
        binding.tvFeedback2?.visibility = android.view.View.VISIBLE
        
        binding.tvFeedback3?.text = "Feedback: Unable to load feedback. Please try again later."
        binding.tvFeedback3?.visibility = android.view.View.VISIBLE
        
        binding.tvTechFeedback?.text = "Tech Feedback: Unable to load technical feedback."
        binding.tvTechFeedback?.visibility = android.view.View.VISIBLE
        
        binding.tvSummary?.text = "Interview completed. Review your answers and practice more to improve your performance."
        binding.tvSummary?.visibility = android.view.View.VISIBLE
    }

    private fun showLoadingState(show: Boolean) {
        // 可以在这里添加加载指示器的显示/隐藏逻辑
        if (show) {
            Toast.makeText(this, "Loading feedback...", Toast.LENGTH_SHORT).show()
        }
    }
} 