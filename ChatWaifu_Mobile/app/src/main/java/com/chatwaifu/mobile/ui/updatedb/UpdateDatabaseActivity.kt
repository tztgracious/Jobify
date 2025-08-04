package com.chatwaifu.mobile.ui.updatedb

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.chatwaifu.mobile.databinding.ActivityUpdateDatabaseBinding
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.RemoveResumeRequest
import com.chatwaifu.mobile.data.network.RemoveResumeResponse
import com.chatwaifu.mobile.data.network.UploadResumeResponse
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

class UpdateDatabaseActivity : AppCompatActivity() {
    private lateinit var binding: ActivityUpdateDatabaseBinding
    private var selectedFileUri: Uri? = null
    private val apiService = JobifyApiService.create()
    private val TAG = "UpdateDatabaseActivity"
    private var docId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUpdateDatabaseBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 获取传递过来的doc_id
        docId = intent.getStringExtra("doc_id")

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
        binding.btnUpload.isEnabled = false
        
        lifecycleScope.launch {
            try {
                // 首先清理现有简历数据
                docId?.let { id ->
                    val removeRequest = RemoveResumeRequest(id = id)
                    val removeResponse = apiService.removeResume(removeRequest)
                    
                    if (removeResponse.isSuccessful) {
                        Log.d(TAG, "Resume removed successfully: ${removeResponse.body()?.message}")
                    } else {
                        Log.w(TAG, "Failed to remove resume: ${removeResponse.code()}")
                        // 继续上传，不因为清理失败而停止
                    }
                }
                
                // 准备文件上传
                val file = createTempFileFromUri(selectedFileUri!!)
                val requestBody = file.asRequestBody("application/pdf".toMediaTypeOrNull())
                val multipartBody = MultipartBody.Part.createFormData("file", file.name, requestBody)
                
                // 上传新文件
                val uploadResponse = apiService.uploadResumeForUpdate(multipartBody)
                
                if (uploadResponse.isSuccessful) {
                    val response = uploadResponse.body()
                    Log.d(TAG, "Upload response: $response")
                    
                    if (response?.valid_file == true) {
                        Toast.makeText(this@UpdateDatabaseActivity, "File uploaded successfully!", Toast.LENGTH_SHORT).show()
                        // 更新doc_id
                        docId = response.id
                    } else {
                        Toast.makeText(this@UpdateDatabaseActivity, "Upload failed: ${response?.error_msg}", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    val errorBody = uploadResponse.errorBody()?.string()
                    Log.e(TAG, "Upload failed: ${uploadResponse.code()}, error: $errorBody")
                    Toast.makeText(this@UpdateDatabaseActivity, "Upload failed: ${uploadResponse.code()}", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error uploading file", e)
                Toast.makeText(this@UpdateDatabaseActivity, "Upload error: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
                binding.btnUpload.isEnabled = true
            }
        }
    }
    
    private fun createTempFileFromUri(uri: Uri): File {
        val inputStream: InputStream = contentResolver.openInputStream(uri)!!
        val tempFile = File.createTempFile("upload_", ".pdf", cacheDir)
        val outputStream = FileOutputStream(tempFile)
        
        inputStream.use { input ->
            outputStream.use { output ->
                input.copyTo(output)
            }
        }
        
        return tempFile
    }
} 