package com.chatwaifu.mobile.ui.welcome

import android.content.Intent
import android.os.Bundle
import android.view.animation.AnimationUtils
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityWelcomeBinding
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity

class WelcomeActivity : AppCompatActivity() {
    private lateinit var binding: ActivityWelcomeBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityWelcomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 启动背景动画
        startBackgroundAnimations()

        // Button
        binding.startButton.setOnClickListener {
            // Jump to ResumeActivity (正确的流程)
            startActivity(Intent(this, UploadResumeActivity::class.java))
            finish()  // Close WelcomeActivity
        }
    }

    private fun startBackgroundAnimations() {
        // 加载动画
        val fadeInOutAnimation = AnimationUtils.loadAnimation(this, R.anim.fade_in_out)
        val scalePulseAnimation = AnimationUtils.loadAnimation(this, R.anim.scale_pulse)
        val rotateSlowAnimation = AnimationUtils.loadAnimation(this, R.anim.rotate_slow)

        // 应用动画到装饰元素
        binding.topDecoration.startAnimation(fadeInOutAnimation)
        binding.topRightDecoration.startAnimation(scalePulseAnimation)
        binding.bottomLeftDecoration.startAnimation(rotateSlowAnimation)
        binding.bottomRightDecoration.startAnimation(fadeInOutAnimation)

        // 设置动画重复
        fadeInOutAnimation.repeatCount = android.view.animation.Animation.INFINITE
        scalePulseAnimation.repeatCount = android.view.animation.Animation.INFINITE
        rotateSlowAnimation.repeatCount = android.view.animation.Animation.INFINITE
    }
}