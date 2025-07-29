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
    private lateinit var viewModel: InterviewQuestionsViewModel
    
    private var currentIndex = 0
    private val answers = mutableListOf<String>()
    private var answerTimer: CountDownTimer? = null
    private var docId: String? = null
    private var answerType: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityInterviewQuestionsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 获取传递的参数
        docId = intent.getStringExtra("doc_id")
        answerType = intent.getStringExtra("answer_type")
        
        Log.d("InterviewQuestionsActivity", "docId: $docId, answerType: $answerType")

        if (answerType == "video") {
            // 跳转到视频回答界面
            val keywords = intent.getStringArrayExtra("keywords")
            val intent = Intent(this, com.chatwaifu.mobile.ui.questions.VideoAnswerActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
            }
            startActivity(intent)
            finish()
            return
        }

        // 初始化ViewModel
        viewModel = ViewModelProvider(this)[InterviewQuestionsViewModel::class.java]
        
        setupUI()
        setupObservers()
        
        // 加载面试问题
        docId?.let { id ->
            viewModel.loadInterviewQuestions(id)
        } ?: run {
            showSnackbar("Error: Missing document ID")
            finish()
        }
    }

    private fun setupUI() {
        binding.btnBack.setOnClickListener { finish() }
        binding.btnNext.setOnClickListener { onNextClicked() }
        // 录视频按钮暂不实现
        binding.btnRecordVideo.text = "Record Video (Coming soon)"
        binding.btnRecordVideo.isEnabled = false
        
        // 初始状态
        binding.btnNext.isEnabled = false
        binding.etAnswer.isEnabled = false
    }
    
    private fun setupObservers() {
        viewModel.questions.observe(this) { questions ->
            Log.d("InterviewQuestionsActivity", "Received ${questions.size} questions")
            if (questions.isNotEmpty()) {
                showCurrentQuestion(questions)
                binding.btnNext.isEnabled = true
                binding.etAnswer.isEnabled = true
                startAnswerTimer()
            }
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            if (isLoading) {
                binding.tvCurrentQuestion.text = "Loading questions..."
                binding.btnNext.isEnabled = false
                binding.etAnswer.isEnabled = false
            }
        }
        
        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                when (error) {
                    "questions_generating" -> {
                        showSnackbar("Questions are still being generated. Please wait...")
                        // 可以在这里实现轮询逻辑
                    }
                    "error_load_failed" -> {
                        showSnackbar("Failed to load questions. Please try again.")
                    }
                    "error_network" -> {
                        showSnackbar("Network error. Please check your connection.")
                    }
                    else -> {
                        showSnackbar("Error: $error")
                    }
                }
            }
        }
    }

    private fun showCurrentQuestion(questions: List<String>) {
        if (currentIndex < questions.size) {
            binding.tvCurrentQuestion.text = questions[currentIndex]
            binding.etAnswer.setText("")
            binding.tilAnswer.hint = "Please enter your answer for question ${currentIndex + 1}..."
            if (currentIndex == questions.size - 1) {
                binding.btnNext.text = "Finish"
            } else {
                binding.btnNext.text = "Next"
            }
        }
    }

    private fun onNextClicked() {
        val answer = binding.etAnswer.text?.toString()?.trim() ?: ""
        if (answer.isEmpty()) {
            showSnackbar("Please enter your answer before proceeding.")
            return
        }
        
        answers.add(answer)
        
        // 提交答案到API
        viewModel.questions.value?.let { questions ->
            if (currentIndex < questions.size) {
                val question = questions[currentIndex]
                docId?.let { id ->
                    viewModel.submitAnswer(id, currentIndex, question, answer, answerType ?: "text")
                }
            }
        }
        
        if (currentIndex < (viewModel.questions.value?.size ?: 0) - 1) {
            currentIndex++
            showCurrentQuestion(viewModel.questions.value ?: emptyList())
            startAnswerTimer()
        } else {
            // 所有问题回答完毕，直接跳转到SolutionActivity
            val intent = Intent(this, com.chatwaifu.mobile.ui.solution.SolutionActivity::class.java)
            intent.putStringArrayListExtra("questions", ArrayList(viewModel.questions.value ?: emptyList()))
            intent.putStringArrayListExtra("answers", ArrayList(answers))
            intent.putStringArrayListExtra("solutions", ArrayList(emptyList())) // 标准答案将在SolutionActivity中获取
            intent.putExtra("doc_id", docId)
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