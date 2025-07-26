package com.chatwaifu.mobile.ui.updatedb

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivityUpdateDatabaseBinding

class UpdateDatabaseActivity : AppCompatActivity() {
    private lateinit var binding: ActivityUpdateDatabaseBinding
    private var selectedFileUri: Uri? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUpdateDatabaseBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnSelectFile.setOnClickListener {
            selectPdfFile()
        }
        binding.btnUpload.setOnClickListener {
            uploadPdfFile()
        }
        binding.btnBack.setOnClickListener {
            // 跳转到TipsActivity
            val intent = Intent(this, com.chatwaifu.mobile.ui.tips.TipsActivity::class.java)
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

    private fun selectPdfFile() {
        val intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.type = "application/pdf"
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        startActivityForResult(Intent.createChooser(intent, "Select PDF"), 1001)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1001 && resultCode == Activity.RESULT_OK) {
            data?.data?.let { uri ->
                selectedFileUri = uri
                binding.tvFileName.text = getFileName(uri)
            }
        }
    }

    private fun getFileName(uri: Uri): String {
        var result = getString(com.chatwaifu.mobile.R.string.no_file_selected)
        if (uri.scheme == "content") {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    result = cursor.getString(cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME))
                }
            }
        } else {
            result = uri.path?.substringAfterLast('/') ?: result
        }
        return result
    }

    private fun uploadPdfFile() {
        if (selectedFileUri == null) {
            Toast.makeText(this, getString(com.chatwaifu.mobile.R.string.no_file_selected), Toast.LENGTH_SHORT).show()
            return
        }
        binding.progressBar.visibility = View.VISIBLE
        // TODO: 实现上传逻辑，上传到后端服务器
        // 这里只做演示，实际应使用OkHttp/Retrofit等上传文件
        binding.progressBar.postDelayed({
            binding.progressBar.visibility = View.GONE
            Toast.makeText(this, getString(com.chatwaifu.mobile.R.string.upload_success), Toast.LENGTH_SHORT).show()
        }, 2000)
    }
} 