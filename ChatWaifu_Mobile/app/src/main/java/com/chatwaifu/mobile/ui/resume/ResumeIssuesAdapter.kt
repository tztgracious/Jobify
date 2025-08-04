package com.chatwaifu.mobile.ui.resume

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.chatwaifu.mobile.databinding.ItemResumeIssueBinding

class ResumeIssuesAdapter(
    private var issues: List<ResumeIssue> = emptyList()
) : RecyclerView.Adapter<ResumeIssuesAdapter.IssueViewHolder>() {

    fun updateIssues(newIssues: List<ResumeIssue>) {
        issues = newIssues
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): IssueViewHolder {
        val binding = ItemResumeIssueBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return IssueViewHolder(binding)
    }

    override fun onBindViewHolder(holder: IssueViewHolder, position: Int) {
        holder.bind(issues[position])
    }

    override fun getItemCount(): Int = issues.size

    class IssueViewHolder(
        private val binding: ItemResumeIssueBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(issue: ResumeIssue) {
            binding.tvIssueTitle.text = issue.title
            binding.tvIssueDescription.text = issue.description
            
            // 根据问题类型设置不同的图标和颜色
            when (issue.type) {
                ResumeIssue.Type.CRITICAL -> {
                    binding.ivIssueIcon.setImageResource(android.R.drawable.ic_dialog_alert)
                    binding.ivIssueIcon.setColorFilter(
                        binding.root.context.getColor(android.R.color.holo_red_dark)
                    )
                }
                ResumeIssue.Type.WARNING -> {
                    binding.ivIssueIcon.setImageResource(android.R.drawable.ic_dialog_alert)
                    binding.ivIssueIcon.setColorFilter(
                        binding.root.context.getColor(android.R.color.holo_orange_dark)
                    )
                }
                ResumeIssue.Type.SUGGESTION -> {
                    binding.ivIssueIcon.setImageResource(android.R.drawable.ic_dialog_info)
                    binding.ivIssueIcon.setColorFilter(
                        binding.root.context.getColor(android.R.color.holo_blue_dark)
                    )
                }
            }
        }
    }
}

data class ResumeIssue(
    val title: String,
    val description: String,
    val type: Type
) {
    enum class Type {
        CRITICAL,    // 严重问题，红色
        WARNING,     // 警告，橙色
        SUGGESTION   // 建议，蓝色
    }
} 