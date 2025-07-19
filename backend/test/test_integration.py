import os
import time

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase


class IntegrationTest(APITestCase):
    def setUp(self):
        self.doc_id = None

    def test_complete_interview_flow(self):
        """
        Test complete user journey through all APIs:
        1. Upload resume
        2. Get keywords 
        3. Set target job
        4. Get interview questions
        5. Submit answers
        6. Get feedback
        """
        print("\n" + "=" * 60)
        print("🔄 INTEGRATION TEST: Complete Interview Flow")
        print("=" * 60)

        # Step 1: Upload Resume
        print("\n📤 Step 1: Upload Resume")
        resume_path = os.path.join(settings.BASE_DIR, 'test', 'fixtures', 'professional_resume.pdf')

        # Read the actual PDF file and create SimpleUploadedFile
        with open(resume_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = SimpleUploadedFile(
            "professional_resume.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(reverse('upload-resume'), {'file': pdf_file})

        self.assertEqual(response.status_code, 201,
                         f"Resume upload failed: {response.data}")  # Expected 201 for created
        response_data = response.json()
        self.assertIn('doc_id', response_data, "No doc_id in upload response")
        self.doc_id = response_data['doc_id']
        print(f"✅ Resume uploaded successfully. Doc ID: {self.doc_id}")

        # Step 2: Get Keywords
        print("\n🔍 Step 2: Get Keywords")
        time.sleep(5)  # Wait for resume processing to complete (adjust as needed)
        print("Waiting for resume parsing to complete...")

        data = {'doc_id': self.doc_id}
        response = self.client.post(reverse('get-keywords'), data, content_type='application/json')

        self.assertIn(response.status_code, [200, 201], f"Get keywords failed: {response.data}")
        response_data = response.json()
        self.assertIn('keywords', response_data, "No keywords in response")
        keywords = response_data['keywords']
        print(
            f"✅ Keywords extracted: {keywords[:100] if keywords else '(empty - parsing issue)'}{'...' if keywords and len(str(keywords)) > 100 else ''}")

        # Step 3: Set Target Job  
        print("\n🎯 Step 3: Set Target Job")
        job_data = {
            'doc_id': self.doc_id,
            'title': 'Software Engineer',
            'description': 'Full-stack software engineer position requiring Python, Django, and React experience.',
            'requirements': 'Bachelor degree in Computer Science, 3+ years experience in web development.'
        }
        response = self.client.post(reverse('target-job'), job_data, content_type='application/json')

        self.assertEqual(response.status_code, 200, f"Target job failed: {response.data}")
        response_data = response.json()
        self.assertIn('message', response_data, "No success message for target job")
        print(f"✅ Target job set successfully: {response_data.get('message', 'Job set')}")

        # Step 4: Get Interview Questions
        print("\n❓ Step 4: Get Interview Questions")
        data = {'doc_id': self.doc_id}
        response = self.client.post(reverse('get-questions'), data, content_type='application/json')

        self.assertIn(response.status_code, [200, 201], f"Get questions failed: {response.data}")
        response_data = response.json()

        # Handle different response formats
        questions = []
        if 'interview_questions' in response_data:
            questions_data = response_data['interview_questions']
            if isinstance(questions_data, str):
                # Parse JSON string if needed
                import json
                try:
                    questions_data = json.loads(questions_data)
                except:
                    pass
            if isinstance(questions_data, list):
                questions = questions_data
        elif 'questions' in response_data:
            questions = response_data['questions']

        self.assertTrue(len(questions) > 0, f"No questions found in response: {response_data}")
        print(f"✅ {len(questions)} interview questions generated")

        # Display first question for verification
        if questions:
            first_question = questions[0] if isinstance(questions[0], str) else str(questions[0])
            print(f"   First question: {first_question[:100]}{'...' if len(first_question) > 100 else ''}")

        # Step 5: Submit Answers
        print("\n✍️  Step 5: Submit Answers to Questions")

        # Generate sample answers for each question
        sample_answers = []
        for i, question in enumerate(questions[:3]):  # Answer first 3 questions
            if isinstance(question, dict) and 'question' in question:
                question_text = question['question']
            else:
                question_text = str(question)

            # Generate contextual sample answers
            if 'experience' in question_text.lower():
                answer = f"I have over 3 years of experience in software development, particularly with Python and Django. In my previous role, I developed several web applications and worked on both frontend and backend components."
            elif 'strength' in question_text.lower() or 'skill' in question_text.lower():
                answer = f"My key strengths include problem-solving, technical communication, and full-stack development. I'm particularly strong in Python, Django, React, and database design."
            elif 'challenge' in question_text.lower() or 'difficult' in question_text.lower():
                answer = f"One significant challenge I faced was optimizing a slow database query that was affecting user experience. I analyzed the query patterns, added proper indexing, and restructured some queries, reducing response time by 70%."
            elif 'team' in question_text.lower():
                answer = f"I work well in collaborative environments and have experience leading small development teams. I believe in clear communication, code reviews, and knowledge sharing to ensure project success."
            elif 'project' in question_text.lower():
                answer = f"I recently worked on a web application that processed user resumes and provided interview preparation. This involved building REST APIs, implementing file upload functionality, and integrating with external AI services."
            else:
                answer = f"This is a great question. Based on my experience in software development and my technical background, I would approach this by first understanding the requirements thoroughly, then designing a scalable solution that follows best practices."

            sample_answers.append({
                'question': question_text,
                'answer': answer
            })

        # Submit each answer
        for i, qa_pair in enumerate(sample_answers):
            answer_data = {
                'doc_id': self.doc_id,
                'question': qa_pair['question'],
                'answer': qa_pair['answer'],
                'question_index': i  # 0-based index as expected by the API
            }

            response = self.client.post(reverse('submit-answer'), answer_data, content_type='application/json')
            self.assertEqual(response.status_code, 200, f"Submit answer {i + 1} failed: {response.data}")
            response_data = response.json()
            self.assertIn('message', response_data, f"No success message for answer {i + 1}")

        print(f"✅ Successfully submitted {len(sample_answers)} answers")

        # Step 6: Get Feedback
        print("\n📝 Step 6: Get Interview Feedback")
        response = self.client.get(reverse('get-feedback'), {'doc_id': self.doc_id})

        self.assertEqual(response.status_code, 200, f"Get feedback failed: {response.data}")
        response_data = response.json()

        # Handle different feedback formats
        feedback_data = None
        if 'feedback' in response_data:
            feedback_data = response_data['feedback']
        elif 'feedbacks' in response_data:
            feedback_data = response_data['feedbacks']

        self.assertIsNotNone(feedback_data, f"No feedback found in response: {response_data}")
        self.assertTrue(len(str(feedback_data).strip()) > 0, "Feedback is empty")

        print(f"✅ Feedback generated successfully")

        # Show detailed feedback if available
        if isinstance(feedback_data, dict):
            if 'summary' in feedback_data:
                print(
                    f"   Summary: {str(feedback_data['summary'])[:150]}{'...' if len(str(feedback_data['summary'])) > 150 else ''}")
            question_feedback_count = len([k for k in feedback_data.keys() if 'feedback' in k])
            if question_feedback_count > 0:
                print(f"   Individual question feedback: {question_feedback_count} questions")
        else:
            print(f"   Feedback preview: {str(feedback_data)[:200]}{'...' if len(str(feedback_data)) > 200 else ''}")

        # Final Success Message
        print(f"\n🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print(f"   📋 Resume uploaded (Doc ID: {self.doc_id})")
        print(f"   🔑 Keywords extracted")
        print(f"   🎯 Target job set")
        print(f"   ❓ {len(questions)} questions generated")
        print(f"   ✍️  {len(sample_answers)} answers submitted")
        print(f"   📝 Feedback received")
        print("=" * 60)
