package com.chatwaifu.mobile.ui.targetjob

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityTargetJobBinding
import com.google.android.material.chip.Chip
import com.google.android.material.snackbar.Snackbar

class TargetJobActivity : AppCompatActivity() {

    private lateinit var binding: ActivityTargetJobBinding
    private lateinit var viewModel: TargetJobViewModel
    private val TAG = "TargetJobActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTargetJobBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        viewModel = ViewModelProvider(this)[TargetJobViewModel::class.java]
        
        setupUI()
        setupObservers()
    }

    private fun setupUI() {
        // 设置标题
        binding.tvTitle.text = getString(R.string.target_job_title)
        
        // 返回按钮
        binding.btnBack.setOnClickListener {
            finish()
        }
        
        // 下一步按钮
        binding.btnNext.setOnClickListener {
            if (validateInputs()) {
                saveTargetJob()
            }
        }
        
        // 预设技能标签
        setupSkillChips()
        
        // 薪资范围选择器
        setupSalaryRangeSpinner()
    }

    private fun setupSkillChips() {
        val commonSkills = listOf(
            "Java", "Kotlin", "Python", "JavaScript", "React", "Vue.js", 
            "Android", "iOS", "Flutter", "Django", "Spring Boot", "Node.js",
            "Docker", "Kubernetes", "AWS", "Azure", "Git", "SQL", "MongoDB",
            "Machine Learning", "Data Science", "UI/UX", "DevOps"
        )
        
        commonSkills.forEach { skill ->
            val chip = Chip(this).apply {
                text = skill
                isCheckable = true
                chipBackgroundColor = ContextCompat.getColorStateList(
                    this@TargetJobActivity, R.color.chip_background_color
                )
            }
            binding.chipGroupSkills.addView(chip)
        }
    }

    private fun setupSalaryRangeSpinner() {
        val salaryRanges = arrayOf(
            "30k-50k", "50k-80k", "80k-120k", "120k-150k", "150k-200k", "200k+"
        )
        // 这里可以设置适配器，暂时用简单的数组
    }

    private fun validateInputs(): Boolean {
        val title = binding.etJobTitle.text.toString().trim()
        val location = binding.etLocation.text.toString().trim()
        
        if (title.isEmpty()) {
            binding.etJobTitle.error = getString(R.string.validation_job_title_required)
            return false
        }
        
        if (location.isEmpty()) {
            binding.etLocation.error = getString(R.string.validation_location_required)
            return false
        }
        
        val selectedSkills = binding.chipGroupSkills.checkedChipIds.map { id ->
            binding.chipGroupSkills.findViewById<Chip>(id).text.toString()
        }
        
        if (selectedSkills.isEmpty()) {
            showSnackbar(getString(R.string.validation_skills_required))
            return false
        }
        
        return true
    }

    private fun saveTargetJob() {
        val title = binding.etJobTitle.text.toString().trim()
        val location = binding.etLocation.text.toString().trim()
        val salaryRange = binding.etSalaryRange.text.toString().trim()
        val selectedSkills = binding.chipGroupSkills.checkedChipIds.map { id ->
            binding.chipGroupSkills.findViewById<Chip>(id).text.toString()
        }
        
        // 获取doc_id，如果没有则使用默认值
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        
        viewModel.saveTargetJob(docId, title, location, salaryRange, selectedSkills)
    }

    private fun setupObservers() {
        viewModel.saveResult.observe(this) { success ->
            if (success) {
                showSnackbar(getString(R.string.success_save))
                // 跳转到下一个页面或返回
                setResult(RESULT_OK)
                finish()
            } else {
                showSnackbar(getString(R.string.error_save_failed))
            }
        }
        
        viewModel.isLoading.observe(this) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
            binding.btnNext.isEnabled = !loading
        }
    }

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
        Log.d(TAG, "Showing Snackbar: $message")
    }

    companion object {
        const val EXTRA_TARGET_JOB_DATA = "target_job_data"
    }
} 