package com.chatwaifu.mobile.ui.answertype

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityAnswerTypeSelectBinding
import com.chatwaifu.mobile.ui.questions.InterviewQuestionsActivity
import com.google.android.material.snackbar.Snackbar

class AnswerTypeSelectActivity : AppCompatActivity() {
    private lateinit var binding: ActivityAnswerTypeSelectBinding
    private var docId: String? = null
    private var keywords: Array<String>? = null
    private var selectedType: String? = null

    // 权限申请回调
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.all { it.value }
        if (allGranted) {
            goToInterviewQuestions("video")
        } else {
            Snackbar.make(binding.root, getString(R.string.permission_denied), Snackbar.LENGTH_LONG).show()
        }
    }

    // 新增：分别处理麦克风和相机权限
    private val micPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        } else {
            Snackbar.make(binding.root, getString(R.string.permission_denied), Snackbar.LENGTH_LONG).show()
        }
    }

    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            goToInterviewQuestions("video")
        } else {
            Snackbar.make(binding.root, getString(R.string.permission_denied), Snackbar.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAnswerTypeSelectBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.tvTitle.text = getString(R.string.select_answer_type)
        binding.btnTextAnswer.text = getString(R.string.text_answer)
        binding.btnVideoAnswer.text = getString(R.string.video_answer)

        docId = intent.getStringExtra("doc_id")
        keywords = intent.getStringArrayExtra("keywords")

        binding.btnTextAnswer.setOnClickListener {
            selectedType = "text"
            binding.btnTextAnswer.isEnabled = false
            binding.btnVideoAnswer.isEnabled = true
        }
        binding.btnVideoAnswer.setOnClickListener {
            selectedType = "video"
            binding.btnTextAnswer.isEnabled = true
            binding.btnVideoAnswer.isEnabled = false
            // 不再触发权限申请和跳转
        }
        binding.btnBack.setOnClickListener {
            val intent = Intent(this, com.chatwaifu.mobile.ui.keywords.KeywordsActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            startActivity(intent)
            finish()
        }
        binding.btnNext.setOnClickListener {
            if (selectedType == null) {
                Snackbar.make(binding.root, getString(R.string.select_answer_type), Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (selectedType == "video") {
                // 先请求麦克风权限，授权后再请求相机
                micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            } else {
                // text answer 直接跳转
                val intent = Intent(this, com.chatwaifu.mobile.ChatActivity::class.java).apply {
                    putExtra("interview_mode", true)
                    putExtra("doc_id", docId)
                    putExtra("model_name", "haru_greeter_t05")
                    putExtra("answer_type", selectedType)
                }
                startActivity(intent)
                finish()
            }
        }
    }

    private fun goToInterviewQuestions(answerType: String) {
        val intent = Intent(this, com.chatwaifu.mobile.ChatActivity::class.java).apply {
            putExtra("interview_mode", true)
            putExtra("doc_id", docId)
            putExtra("model_name", "haru_greeter_t05")
            putExtra("answer_type", answerType)
        }
        startActivity(intent)
        finish()
    }

    // 原checkAndRequestPermissions方法可删除或保留不再使用
} 