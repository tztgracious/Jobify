package com.chatwaifu.mobile.ui.tips

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivityTipsBinding

class TipsActivity : AppCompatActivity() {
    private lateinit var binding: ActivityTipsBinding
    private val viewModel: TipsViewModel by viewModels()
    
    // 保存从SolutionActivity传递过来的数据
    private var questions: ArrayList<String>? = null
    private var answers: ArrayList<String>? = null
    private var solutions: ArrayList<String>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTipsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 保存传递过来的数据
        questions = intent.getStringArrayListExtra("questions")
        answers = intent.getStringArrayListExtra("answers")
        solutions = intent.getStringArrayListExtra("solutions")

        // 绑定ViewModel数据到UI
        viewModel.tips.observe(this) { tips ->
            binding.tvTip1Title.text = tips[0].title
            binding.tvTip1Desc.text = tips[0].description
            binding.tvTip2Title.text = tips[1].title
            binding.tvTip2Desc.text = tips[1].description
            binding.tvTip3Title.text = tips[2].title
            binding.tvTip3Desc.text = tips[2].description
        }

        binding.btnBack.setOnClickListener {
            // 跳转到SolutionActivity并传递数据
            val intent = Intent(this, com.chatwaifu.mobile.ui.solution.SolutionActivity::class.java)
            questions?.let { intent.putStringArrayListExtra("questions", it) }
            answers?.let { intent.putStringArrayListExtra("answers", it) }
            solutions?.let { intent.putStringArrayListExtra("solutions", it) }
            startActivity(intent)
            finish()
        }
        binding.btnHelpUpdateDatabase.setOnClickListener {
            // 跳转到UpdateDatabaseActivity
            val intent = Intent(this, com.chatwaifu.mobile.ui.updatedb.UpdateDatabaseActivity::class.java)
            startActivity(intent)
            finish()
        }
        binding.btnFinish.setOnClickListener {
            // 返回主界面或欢迎页
            val intent = Intent(this, com.chatwaifu.mobile.ui.welcome.WelcomeActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            startActivity(intent)
            finish()
        }
    }
} 