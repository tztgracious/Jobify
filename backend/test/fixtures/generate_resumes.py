#!/usr/bin/env python3
"""
Professional Resume Generator
Generates realistic PDF resumes for various professions with random data.
"""

import random
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# Fake data pools
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn",
    "Blake", "Cameron", "Dakota", "Emerson", "Hayden", "Jamie", "Kai", "Logan",
    "Parker", "Reese", "Sage", "Sidney", "Skylar", "Teagan", "Kendall", "Peyton"
]

LAST_NAMES = [
    "Anderson", "Brown", "Davis", "Garcia", "Johnson", "Jones", "Miller", "Moore",
    "Rodriguez", "Smith", "Taylor", "Thomas", "Williams", "Wilson", "Martinez",
    "Jackson", "White", "Harris", "Clark", "Lewis", "Robinson", "Walker", "Hall"
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Boston", "Nashville", "Detroit", "Portland", "Memphis"
]

STATES = [
    "NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "NC", "WA", "CO", "MA",
    "TN", "MI", "OR", "NV", "GA", "VA", "MD", "MN", "WI", "UT", "CT", "NJ"
]

# Professional profiles with skills and experience
PROFESSIONS = {
    "Software Engineer": {
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "Django", "PostgreSQL",
            "AWS", "Docker", "Git", "REST APIs", "GraphQL", "MongoDB", "Redis",
            "Kubernetes", "CI/CD", "Agile", "TDD", "Microservices"
        ],
        "companies": [
            "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber",
            "Airbnb", "Spotify", "Slack", "Zoom", "Dropbox", "Square", "Stripe"
        ],
        "responsibilities": [
            "Developed scalable web applications serving millions of users",
            "Implemented RESTful APIs and microservices architecture",
            "Optimized database queries improving performance by 40%",
            "Led code reviews and mentored junior developers",
            "Collaborated with cross-functional teams in Agile environment",
            "Built CI/CD pipelines reducing deployment time by 60%",
            "Designed and implemented real-time chat features",
            "Migrated legacy systems to modern cloud infrastructure"
        ]
    },
    "Data Scientist": {
        "skills": [
            "Python", "R", "SQL", "TensorFlow", "PyTorch", "Scikit-learn",
            "Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter", "AWS",
            "Docker", "Git", "Statistics", "Machine Learning", "Deep Learning"
        ],
        "companies": [
            "Google", "Microsoft", "Amazon", "IBM", "Salesforce", "LinkedIn",
            "Tesla", "Palantir", "Databricks", "Snowflake", "DataBricks", "Nvidia"
        ],
        "responsibilities": [
            "Built predictive models increasing revenue by 25%",
            "Analyzed large datasets to identify business insights",
            "Developed recommendation systems improving user engagement",
            "Created automated ML pipelines for model deployment",
            "Collaborated with stakeholders to define KPIs and metrics",
            "Implemented A/B testing frameworks for product features",
            "Optimized marketing campaigns using customer segmentation",
            "Built real-time analytics dashboards for executive team"
        ]
    },
    "Marketing Manager": {
        "skills": [
            "Digital Marketing", "SEO", "SEM", "Google Analytics", "Facebook Ads",
            "Content Marketing", "Email Marketing", "Social Media", "Branding",
            "Campaign Management", "A/B Testing", "Lead Generation", "CRM"
        ],
        "companies": [
            "Nike", "Coca-Cola", "Procter & Gamble", "Unilever", "Johnson & Johnson",
            "L'Oréal", "Nestlé", "PepsiCo", "Adidas", "Samsung", "Sony", "Intel"
        ],
        "responsibilities": [
            "Managed $2M annual marketing budget across multiple channels",
            "Increased brand awareness by 45% through integrated campaigns",
            "Led social media strategy reaching 500K+ followers",
            "Optimized conversion rates improving ROI by 35%",
            "Coordinated cross-functional teams for product launches",
            "Analyzed market trends and competitor strategies",
            "Developed content calendar and brand guidelines",
            "Managed partnerships with influencers and agencies"
        ]
    },
    "Product Manager": {
        "skills": [
            "Product Strategy", "User Research", "Agile", "Scrum", "Jira",
            "Analytics", "A/B Testing", "Wireframing", "SQL", "Data Analysis",
            "Stakeholder Management", "Roadmap Planning", "Go-to-Market"
        ],
        "companies": [
            "Google", "Microsoft", "Amazon", "Apple", "Meta", "Spotify",
            "Slack", "Zoom", "Notion", "Figma", "Canva", "Shopify", "Square"
        ],
        "responsibilities": [
            "Defined product roadmap and strategy for core features",
            "Conducted user research and usability testing",
            "Collaborated with engineering teams to deliver products",
            "Analyzed metrics and KPIs to drive product decisions",
            "Managed product backlog and sprint planning",
            "Led go-to-market strategies for new feature launches",
            "Coordinated with design team on user experience",
            "Presented product updates to executive leadership"
        ]
    },
    "UX Designer": {
        "skills": [
            "Figma", "Sketch", "Adobe Creative Suite", "Prototyping", "Wireframing",
            "User Research", "Usability Testing", "Design Systems", "HTML/CSS",
            "JavaScript", "Information Architecture", "Interaction Design"
        ],
        "companies": [
            "Apple", "Google", "Microsoft", "Adobe", "Figma", "Airbnb",
            "Uber", "Netflix", "Spotify", "Dropbox", "Slack", "Zoom", "Notion"
        ],
        "responsibilities": [
            "Designed user interfaces for web and mobile applications",
            "Conducted user research and created personas",
            "Built interactive prototypes and design systems",
            "Collaborated with product managers and developers",
            "Performed usability testing and iterated on designs",
            "Created wireframes and high-fidelity mockups",
            "Established design guidelines and component libraries",
            "Presented design concepts to stakeholders"
        ]
    },
    "DevOps Engineer": {
        "skills": [
            "AWS", "Docker", "Kubernetes", "Terraform", "Jenkins", "Git",
            "Linux", "Python", "Bash", "Ansible", "Prometheus", "Grafana",
            "CI/CD", "Infrastructure as Code", "Monitoring", "Security"
        ],
        "companies": [
            "Amazon", "Google", "Microsoft", "Netflix", "Uber", "Airbnb",
            "Spotify", "Dropbox", "Slack", "HashiCorp", "Atlassian", "GitLab"
        ],
        "responsibilities": [
            "Built and maintained CI/CD pipelines for 50+ microservices",
            "Automated infrastructure deployment using Terraform",
            "Managed Kubernetes clusters serving millions of requests",
            "Implemented monitoring and alerting systems",
            "Optimized cloud costs reducing expenses by 30%",
            "Ensured 99.9% uptime for critical production systems",
            "Collaborated with development teams on deployment strategies",
            "Maintained security compliance and best practices"
        ]
    }
}

UNIVERSITIES = [
    "Stanford University", "MIT", "Harvard University", "UC Berkeley",
    "Carnegie Mellon University", "University of Washington", "Georgia Tech",
    "University of Illinois", "University of Michigan", "Cornell University",
    "University of Texas at Austin", "UCLA", "UC San Diego", "Caltech"
]

DEGREES = [
    "Bachelor of Science in Computer Science",
    "Bachelor of Science in Data Science",
    "Bachelor of Business Administration",
    "Bachelor of Science in Engineering",
    "Master of Science in Computer Science",
    "Master of Business Administration",
    "Master of Science in Data Science"
]

def generate_fake_person():
    """Generate a fake person with profession and details"""
    profession = random.choice(list(PROFESSIONS.keys()))
    profile = PROFESSIONS[profession]
    
    return {
        "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "profession": profession,
        "email": f"{random.choice(FIRST_NAMES).lower()}.{random.choice(LAST_NAMES).lower()}@email.com",
        "phone": f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "location": f"{random.choice(CITIES)}, {random.choice(STATES)}",
        "skills": random.sample(profile["skills"], random.randint(8, 12)),
        "companies": profile["companies"],
        "responsibilities": profile["responsibilities"],
        "university": random.choice(UNIVERSITIES),
        "degree": random.choice(DEGREES),
        "gpa": round(random.uniform(3.2, 4.0), 2)
    }

def generate_experience(person):
    """Generate work experience for a person"""
    experiences = []
    current_year = datetime.now().year
    years_experience = random.randint(2, 8)
    
    for i in range(random.randint(2, 4)):
        company = random.choice(person["companies"])
        
        # Calculate dates
        end_year = current_year - (i * random.randint(1, 2))
        start_year = end_year - random.randint(1, 3)
        
        # Ensure we don't go too far back
        if start_year < current_year - years_experience:
            start_year = current_year - years_experience
        
        # Format dates
        if i == 0:  # Current job
            date_range = f"{start_year} - Present"
        else:
            date_range = f"{start_year} - {end_year}"
        
        # Generate responsibilities
        responsibilities = random.sample(
            person["responsibilities"], 
            random.randint(3, 5)
        )
        
        experiences.append({
            "title": person["profession"],
            "company": company,
            "dates": date_range,
            "responsibilities": responsibilities
        })
    
    return experiences

def create_professional_resume_pdf(filename="resume.pdf"):
    """Create a professional-looking resume PDF"""
    person = generate_fake_person()
    experiences = generate_experience(person)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=3
    )
    
    # Build the document
    story = []
    
    # Header
    story.append(Paragraph(person["name"], title_style))
    story.append(Paragraph(person["profession"], subtitle_style))
    
    # Contact info
    contact_info = f"{person['email']} | {person['phone']} | {person['location']}"
    story.append(Paragraph(contact_info, subtitle_style))
    story.append(Spacer(1, 12))
    
    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    summary = f"Experienced {person['profession'].lower()} with {random.randint(3, 8)} years of expertise in {', '.join(person['skills'][:3])}. Proven track record of delivering high-quality solutions and driving business results through innovative technology implementations."
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
    
    for exp in experiences:
        # Job title and company
        job_header = f"<b>{exp['title']}</b> | {exp['company']}"
        story.append(Paragraph(job_header, styles['Normal']))
        
        # Dates
        story.append(Paragraph(exp['dates'], styles['Normal']))
        story.append(Spacer(1, 6))
        
        # Responsibilities
        for resp in exp['responsibilities']:
            story.append(Paragraph(f"• {resp}", styles['Normal']))
        
        story.append(Spacer(1, 12))
    
    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_style))
    skills_text = " | ".join(person['skills'])
    story.append(Paragraph(skills_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Education
    story.append(Paragraph("EDUCATION", section_style))
    education = f"<b>{person['degree']}</b><br/>{person['university']}<br/>GPA: {person['gpa']}"
    story.append(Paragraph(education, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    # Save to file
    buffer.seek(0)
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    buffer.close()
    
    print(f"✅ Generated resume: {filename}")
    print(f"👤 Name: {person['name']}")
    print(f"💼 Profession: {person['profession']}")
    print(f"📧 Email: {person['email']}")
    print(f"📍 Location: {person['location']}")
    
    return filename

def create_simple_resume_pdf(filename="simple_resume.pdf"):
    """Create a simple resume PDF (similar to your existing function)"""
    person = generate_fake_person()
    experiences = generate_experience(person)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    y = height - 80
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, person["name"])
    
    y -= 30
    c.setFont("Helvetica", 14)
    c.drawString(50, y, person["profession"])
    
    y -= 25
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"{person['email']} | {person['phone']} | {person['location']}")
    
    # Experience Section
    y -= 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "PROFESSIONAL EXPERIENCE")
    
    y -= 30
    for exp in experiences[:2]:  # Show only 2 experiences for simplicity
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{exp['title']} | {exp['company']}")
        
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, exp['dates'])
        
        y -= 20
        for resp in exp['responsibilities'][:3]:  # Show only 3 responsibilities
            c.setFont("Helvetica", 10)
            c.drawString(70, y, f"• {resp}")
            y -= 15
        
        y -= 20
    
    # Skills Section
    y -= 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "TECHNICAL SKILLS")
    
    y -= 25
    c.setFont("Helvetica", 11)
    skills_text = ", ".join(person['skills'][:8])
    c.drawString(50, y, skills_text)
    
    # Education Section
    y -= 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "EDUCATION")
    
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(50, y, person['degree'])
    y -= 15
    c.drawString(50, y, person['university'])
    
    c.save()
    
    # Save to file
    buffer.seek(0)
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    buffer.close()
    
    print(f"✅ Generated simple resume: {filename}")
    print(f"👤 Name: {person['name']}")
    print(f"💼 Profession: {person['profession']}")
    
    return filename

def generate_multiple_resumes(count=5):
    """Generate multiple resumes with different professions"""
    filenames = []
    
    for i in range(count):
        filename = f"resume_{i+1}.pdf"
        if i % 2 == 0:
            create_professional_resume_pdf(filename)
        else:
            create_simple_resume_pdf(filename)
        filenames.append(filename)
    
    print(f"\n🎉 Generated {count} resumes successfully!")
    return filenames

if __name__ == "__main__":
    # Generate a single professional resume
    print("🚀 Generating professional resume...")
    create_professional_resume_pdf("professional_resume.pdf")
    
    print("\n" + "="*50)
    
    # Generate a simple resume
    print("🚀 Generating simple resume...")
    create_simple_resume_pdf("simple_resume.pdf")
    
    print("\n" + "="*50)
    
    # Generate multiple resumes
    print("🚀 Generating multiple resumes...")
    generate_multiple_resumes(3)
