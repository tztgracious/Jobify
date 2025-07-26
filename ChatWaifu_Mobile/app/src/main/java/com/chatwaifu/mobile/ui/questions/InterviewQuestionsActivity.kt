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
import android.os.CountDownTimer
import android.widget.Toast

class InterviewQuestionsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityInterviewQuestionsBinding
    private val questions = listOf(
        "Please introduce yourself.",
        "Why are you interested in this position?",
        "Describe the biggest technical challenge you've faced."
    )
    private var currentIndex = 0
    private val answers = mutableListOf<String>()
    private var answerTimer: CountDownTimer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityInterviewQuestionsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val answerType = intent.getStringExtra("answer_type")
        if (answerType == "video") {
            // 跳转到视频回答界面
            val docId = intent.getStringExtra("doc_id")
            val keywords = intent.getStringArrayExtra("keywords")
            val intent = Intent(this, com.chatwaifu.mobile.ui.questions.VideoAnswerActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
            }
            startActivity(intent)
            finish()
            return
        }

        setupUI()
        showCurrentQuestion()
        startAnswerTimer()
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
            startAnswerTimer()
        } else {
            // 跳转到TipsActivity并传递答案
            val intent = Intent(this, com.chatwaifu.mobile.ui.tips.TipsActivity::class.java)
            intent.putStringArrayListExtra("answers", ArrayList(answers))
            startActivity(intent)
            finish()
        }
    }

    private fun startAnswerTimer() {
        binding.tvTimer?.visibility = View.VISIBLE
        binding.tvTimer?.text = "60s"
        answerTimer?.cancel()
        answerTimer = object : CountDownTimer(60_000, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                binding.tvTimer?.text = "${millisUntilFinished / 1000}s"
            }
            override fun onFinish() {
                binding.tvTimer?.text = "0s"
                binding.etAnswer.isEnabled = false
                binding.btnNext.isEnabled = false
                Toast.makeText(this@InterviewQuestionsActivity, getString(R.string.time_up), Toast.LENGTH_SHORT).show()
            }
        }.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        answerTimer?.cancel()
    }

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
        Log.d("InterviewQuestionsActivity", "Showing Snackbar: $message")
    }

    companion object {
        const val EXTRA_DOC_ID = "doc_id"
    }
} 