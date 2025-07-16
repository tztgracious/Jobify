package com.chatwaifu.mobile.ui.questions

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityInterviewQuestionsBinding
import com.google.android.material.snackbar.Snackbar

class InterviewQuestionsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityInterviewQuestionsBinding
    private val questions = listOf(
        "Please introduce yourself.",
        "Why are you interested in this position?",
        "Describe the biggest technical challenge you've faced."
    )
    private var currentIndex = 0
    private val answers = mutableListOf<String>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityInterviewQuestionsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        showCurrentQuestion()
    }

    private fun setupUI() {
        binding.btnBack.setOnClickListener { finish() }
        binding.btnNext.setOnClickListener { onNextClicked() }
        // 录视频按钮暂不实现
        binding.btnRecordVideo.text = "Record Video (Coming soon)"
        binding.btnRecordVideo.isEnabled = false
    }

    private fun showCurrentQuestion() {
        binding.tvCurrentQuestion.text = questions[currentIndex]
        binding.etAnswer.setText("")
        binding.tilAnswer.hint = "Please enter your answer for question ${currentIndex + 1}..."
        if (currentIndex == questions.size - 1) {
            binding.btnNext.text = "Finish"
        } else {
            binding.btnNext.text = "Next"
        }
    }

    private fun onNextClicked() {
        val answer = binding.etAnswer.text?.toString()?.trim() ?: ""
        answers.add(answer)
        if (currentIndex < questions.size - 1) {
            currentIndex++
            showCurrentQuestion()
        } else {
            // 跳转到TipsActivity并传递答案
            val intent = Intent(this, TipsActivity::class.java)
            intent.putStringArrayListExtra("answers", ArrayList(answers))
            startActivity(intent)
            finish()
        }
    }

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
        Log.d("InterviewQuestionsActivity", "Showing Snackbar: $message")
    }

    companion object {
        const val EXTRA_DOC_ID = "doc_id"
    }
} 