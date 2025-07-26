package com.chatwaifu.mobile.ui.answermode

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.ui.keywords.KeywordsActivity
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.unit.Dp
import androidx.compose.runtime.livedata.observeAsState
import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.result.ActivityResultLauncher
import androidx.core.content.ContextCompat
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Scaffold
import kotlinx.coroutines.launch
import androidx.lifecycle.lifecycleScope

class AnswerModeSelectActivity : AppCompatActivity() {
    
    private val viewModel: AnswerModeViewModel by viewModels()
    private lateinit var requestPermissionsLauncher: ActivityResultLauncher<Array<String>>
    private val snackbarHostState = SnackbarHostState()
    private lateinit var docId: String
    private lateinit var keywords: Array<String>

    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 获取从KeywordsActivity传递过来的参数
        docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")

        requestPermissionsLauncher = registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->
            val granted = permissions[Manifest.permission.CAMERA] == true &&
                          permissions[Manifest.permission.RECORD_AUDIO] == true
            if (granted) {
                goToChatActivity("video")
            } else {
                lifecycleScope.launch {
                    snackbarHostState.showSnackbar("Camera and microphone permissions are required for video answer.")
                }
            }
        }

        setContentView(ComposeView(this).apply {
            setContent {
                MaterialTheme {
                    Scaffold(
                        snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
                    ) { padding ->
                        AnswerModeSelectScreen(
                            viewModel = viewModel,
                            onModeSelected = { mode ->
                                if (mode == "video") {
                                    val cameraGranted = ContextCompat.checkSelfPermission(this@AnswerModeSelectActivity, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
                                    val audioGranted = ContextCompat.checkSelfPermission(this@AnswerModeSelectActivity, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
                                    if (cameraGranted && audioGranted) {
                                        goToChatActivity("video")
                                    } else {
                                        requestPermissionsLauncher.launch(arrayOf(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO))
                                    }
                                } else {
                                    goToChatActivity("text")
                                }
                            },
                            onBackPressed = {
                                // 返回到KeywordsActivity
                                val intent = Intent(this@AnswerModeSelectActivity, KeywordsActivity::class.java)
                                intent.putExtra("doc_id", docId)
                                intent.putExtra("keywords", keywords)
                                startActivity(intent)
                                finish()
                            },
                            modifier = Modifier.padding(padding)
                        )
                    }
                }
            }
        })
    }

    private fun goToChatActivity(mode: String) {
        val intent = Intent(this@AnswerModeSelectActivity, ChatActivity::class.java)
        intent.putExtra("answer_mode", mode)
        intent.putExtra("doc_id", docId)
        intent.putExtra("keywords", keywords)
        startActivity(intent)
        finish()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnswerModeSelectScreen(
    viewModel: AnswerModeViewModel,
    onModeSelected: (String) -> Unit,
    onBackPressed: () -> Unit,
    modifier: Modifier = Modifier
) {
    val answerModes by viewModel.answerModes.observeAsState(emptyList())
    val selectedMode by viewModel.selectedMode.observeAsState()
    val isLoading by viewModel.isLoading.observeAsState(false)
    val error by viewModel.error.observeAsState("")
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(Color(0xFF4285F4), Color(0xFFB3C6F7))
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 标题
            Text(
                text = "Please select your answer mode",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .padding(top = 32.dp, bottom = 8.dp)
            )
            // 副标题
            Text(
                text = "Please choose how you want to answer the following questions.",
                fontSize = 16.sp,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(bottom = 40.dp)
            )

            // 卡片包裹按钮
            Card(
                shape = RoundedCornerShape(24.dp),
                elevation = CardDefaults.cardElevation(12.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 32.dp)
            ) {
                Column(
                    modifier = Modifier
                        .background(Color.White)
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    for ((index, mode) in answerModes.withIndex()) {
                        if (index > 0) {
                            Spacer(modifier = Modifier.height(20.dp))
                        }
                        
                        Button(
                            onClick = { onModeSelected(mode.mode) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(56.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (mode.mode == "text") Color(0xFF4285F4) else Color(0xFF34A853)
                            ),
                            shape = RoundedCornerShape(16.dp),
                            elevation = ButtonDefaults.buttonElevation(8.dp)
                        ) {
                            Icon(
                                imageVector = if (mode.mode == "text") Icons.Filled.Edit else Icons.Filled.Videocam,
                                contentDescription = mode.title,
                                tint = Color.White,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = mode.title,
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // 返回按钮
            OutlinedButton(
                onClick = onBackPressed,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                shape = RoundedCornerShape(16.dp),
                border = BorderStroke(1.dp, Color.White)
            ) {
                Text(
                    text = "Back to Job Selection",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
        }
    }
} 