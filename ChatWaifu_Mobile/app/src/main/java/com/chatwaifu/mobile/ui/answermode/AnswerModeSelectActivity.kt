package com.chatwaifu.mobile.ui.answermode

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
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

class AnswerModeSelectActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 获取从KeywordsActivity传递过来的参数
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
        
        setContentView(ComposeView(this).apply {
            setContent {
                MaterialTheme {
                    AnswerModeSelectScreen(
                        onModeSelected = { mode ->
                            // 保存选择的模式并跳转到聊天界面，传递所有参数
                            val intent = Intent(this@AnswerModeSelectActivity, ChatActivity::class.java)
                            intent.putExtra("answer_mode", mode)
                            intent.putExtra("doc_id", docId)
                            intent.putExtra("keywords", keywords)
                            startActivity(intent)
                            finish()
                        },
                        onBackPressed = {
                            // 返回到KeywordsActivity
                            val intent = Intent(this@AnswerModeSelectActivity, KeywordsActivity::class.java)
                            intent.putExtra("doc_id", docId)
                            intent.putExtra("keywords", keywords)
                            startActivity(intent)
                            finish()
                        }
                    )
                }
            }
        })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnswerModeSelectScreen(
    onModeSelected: (String) -> Unit,
    onBackPressed: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 顶部标题
        Text(
            text = "Please select your answer type",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color.Gray,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 80.dp, bottom = 60.dp)
        )
        
        // 选项区域 - 居中
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // TEXT ANSWER 按钮 - 蓝色
            Button(
                onClick = { onModeSelected("text") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(60.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF4285F4)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "TEXT ANSWER",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // VIDEO ANSWER 按钮 - 也是蓝色
            Button(
                onClick = { onModeSelected("video") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(60.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF4285F4)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "VIDEO ANSWER",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
        }
        
        // 底部只保留BACK按钮
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 20.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            Button(
                onClick = onBackPressed,
                modifier = Modifier.height(50.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF4285F4)
                ),
                shape = RoundedCornerShape(12.dp)
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