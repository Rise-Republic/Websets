# 🎯 Websets Mining Job Prompt Optimization Guide

## Overview

This guide explains how to craft optimal prompts for Websets mining jobs to achieve the best data extraction results. The Websets system uses LLM-powered agents (GPT-4/Claude) to intelligently discover, crawl, and extract structured data from the web based on natural language prompts.

## 📝 Prompt Structure Framework

### Core Components (Required)

1. **Target Entity/Subject** - What you're looking for (companies, research papers, products, people)
2. **Domain/Industry** - Specific field or sector
3. **Geographic Scope** - Location constraints (if relevant)
4. **Specific Criteria** - Measurable filters (size, stage, technology)

### Optional Enhancements

- **Data Type Hints** - Expected format (tables, lists, directories)
- **Timeframe** - Recent, specific years, date ranges
- **Quality Indicators** - Authority, size, verification criteria

## ✅ Optimal Prompt Patterns

### Excellent Examples

```bash
# Startup/Company Discovery
"AI startups in Europe hiring ML engineers"
"SaaS companies in Silicon Valley with Series A funding"
"Fintech companies with 50-200 employees in New York"
"Y Combinator startups from 2023 batch working on healthcare"
"Bootstrapped B2B software companies in Austin"

# Research/Academic
"Recent machine learning research papers from top conferences"
"Computer vision papers published in 2023 with code availability"
"NLP research from AAAI, ICML, NeurIPS conferences"

# Industry Analysis
"Electric vehicle manufacturers with production capacity data"
"Renewable energy companies with project portfolios"
"Cybersecurity vendors with enterprise customer lists"

# Investment/Funding
"Series B startups in biotech with FDA approvals"
"Venture capital firms investing in climate tech"
"Private equity deals in healthcare technology 2023"
```

### ❌ Poor Examples (Avoid These)

```bash
"Companies"                    # Too broad
"AI stuff"                     # Vague terminology
"Good startups"               # Subjective criteria
"Everything about tech"       # Unfocused scope
"Best companies to work for"  # Opinion-based
```

## 🤖 How LLM Agents Process Your Prompt

### 1. PlannerAgent (GPT-4)
- **Input**: Your natural language prompt
- **Output**: Structured execution plan
- **Process**:
  - Analyzes target entities and criteria
  - Generates search keywords and strategies
  - Identifies target website categories
  - Estimates scope (typically 50-100 URLs)
  - Defines quality criteria and expected data structures

### 2. DiscoveryAgent
- **Input**: Execution plan from PlannerAgent
- **Output**: Prioritized list of URLs
- **Process**:
  - Generates 20-30 high-quality URLs per search strategy
  - Focuses on pages with structured data (tables, lists, directories)
  - Targets authoritative, well-structured websites
  - Supports both search engine discovery and direct site targeting
  - Applies automatic deduplication and priority scoring

### 3. Schema Inference Agent
- **Input**: Crawled web pages
- **Output**: Structured data extraction
- **Process**:
  - Automatically detects data structures without manual configuration
  - Adapts to tables, lists, text, and structured data formats
  - Creates intelligent field mappings based on content analysis
  - Handles various data types and formats dynamically

## 🎛️ Advanced Parameters and Options

### CLI Script Usage

```bash
# Basic usage
python scripts/run_job.py "Your prompt here"

# Advanced options
python scripts/run_job.py "AI startups in Europe" \
  --user-email user@example.com \
  --sync  # Run synchronously (blocking)
```

### API Parameters (JSON)

```json
{
  "prompt": "Your mining query",
  "estimated_urls": 100,          // Max URLs to process (default: 50)
  "complexity": "medium",         // low|medium|high
  "target_categories": [          // Optional site categories
    "startup_directories",
    "company_databases",
    "industry_reports"
  ],
  "quality_criteria": [           // Optional quality filters
    "structured_data_present",
    "authoritative_source",
    "recent_content"
  ]
}
```

## 🎯 Optimization Strategies

### Specificity Levels

| Level | Example | Result Quality |
|-------|---------|----------------|
| **Too Broad** | "Tech companies" | Poor targeting, noisy results |
| **Good** | "AI startups in Europe" | Better focus, moderate quality |
| **Optimal** | "AI startups in Europe hiring ML engineers" | Best results, high relevance |

### Include Measurable Criteria

- **Funding Stage**: "Series A", "seed funding", "bootstrapped", "IPO"
- **Company Size**: "50-200 employees", "enterprise", "startup", "Fortune 500"
- **Technology Stack**: "machine learning", "blockchain", "SaaS", "mobile apps"
- **Timeframe**: "2023", "recent", "last 6 months", "founded after 2020"
- **Geographic**: "Silicon Valley", "Europe", "Asia-Pacific", "remote-first"

### Data Type Hints for Better Extraction

```bash
# Hint at expected data structures
"companies with employee directories and contact information"
"research papers with citation counts and author affiliations"
"products with detailed pricing tables and feature comparisons"
"startups with funding history and investor information"
"conferences with speaker lists and session schedules"
```

### Industry-Specific Patterns

```bash
# Healthcare/Biotech
"FDA-approved medical device companies with revenue data"
"Clinical trial sponsors in oncology with phase 3 studies"

# Finance/Fintech
"Digital banking startups with regulatory approvals"
"Cryptocurrency exchanges with trading volume statistics"

# Enterprise Software
"CRM vendors with customer case studies and pricing"
"DevOps tools with GitHub integration and user metrics"

# E-commerce/Retail
"D2C brands with Shopify stores and social media presence"
"Amazon FBA sellers with product review analytics"
```

## 📊 Expected Results and Performance

### Typical Output Metrics

- **URLs Discovered**: 20-100 per job (configurable)
- **Success Rate**: 70-90% for well-crafted prompts
- **Data Quality**: Automatic schema detection and validation
- **Processing Time**: 5-30 minutes depending on scope
- **Priority Scoring**: 1-5 scale (1 = highest priority)

### Data Export Formats

- **JSON**: Structured data with metadata
- **CSV**: Tabular format for analysis
- **API Access**: Real-time querying and filtering
- **Vector Search**: Semantic search capabilities

## 🔍 Quality Factors for Success

### High-Quality Prompts Include

1. **Specific Entity Types**: Companies, papers, products (not generic "things")
2. **Measurable Criteria**: Numbers, dates, categories, stages
3. **Domain Expertise**: Industry-specific terminology
4. **Realistic Scope**: Focused enough to be actionable
5. **Data Structure Hints**: Expected formats and fields

### Common Pitfalls to Avoid

- **Over-generalization**: "All companies in tech"
- **Subjective criteria**: "Best", "top", "good"
- **Unmeasurable attributes**: "Innovative", "disruptive"
- **Too many constraints**: Overly narrow scope
- **Ambiguous terminology**: Industry jargon without context

## 🚀 Advanced Use Cases

### Multi-Stage Queries

```bash
# Stage 1: Broad discovery
"Y Combinator portfolio companies in healthcare"

# Stage 2: Refined targeting
"Y Combinator healthcare startups with FDA partnerships"

# Stage 3: Specific data points
"Y Combinator healthcare startups with FDA partnerships and Series A funding"
```

### Comparative Analysis

```bash
"Competitor analysis: Slack alternatives with enterprise features"
"Market research: CRM platforms vs Salesforce pricing comparison"
"Technology stack: React component libraries with TypeScript support"
```

### Temporal Tracking

```bash
"Unicorn startups that achieved $1B valuation in 2023"
"IPO filings in biotech sector Q4 2023"
"Acquisition announcements in cybersecurity 2023"
```

## 📈 Monitoring and Optimization

### Job Performance Metrics

- Monitor job completion rates
- Track data extraction quality scores
- Analyze URL discovery success rates
- Review schema inference accuracy

### Iterative Improvement

1. **Start Broad**: Initial discovery with general terms
2. **Analyze Results**: Review extracted data quality
3. **Refine Prompt**: Add specific criteria based on findings
4. **Re-run**: Execute refined query for better results

### Debugging Poor Results

- **Too few results**: Broaden geographic or industry scope
- **Low quality data**: Add more specific criteria
- **Irrelevant results**: Include negative keywords or constraints
- **Missing data**: Hint at expected data structures

## 🔧 Technical Configuration

### Environment Variables

```bash
# Required for LLM agents
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  # Optional

# Performance tuning
MAX_CONCURRENT_CRAWLS=5
REQUEST_DELAY_MS=1000
CRAWL_TIMEOUT_SECONDS=30
```

### System Limits

- **Max URLs per job**: 100 (configurable)
- **Concurrent crawls**: 5 (adjustable)
- **Request delays**: 1 second (respectful crawling)
- **Timeout**: 30 seconds per page

## 📚 Examples by Industry

### Technology Startups

```bash
"AI/ML startups in San Francisco with venture funding"
"DevOps tool companies with GitHub marketplace presence"
"Cybersecurity startups founded by ex-FAANG engineers"
"No-code/low-code platforms with enterprise customers"
```

### Healthcare & Biotech

```bash
"Digital health startups with FDA breakthrough device designation"
"Pharmaceutical companies with COVID-19 vaccine development"
"Medical device manufacturers with CE marking in Europe"
"Telemedicine platforms with insurance partnerships"
```

### Financial Services

```bash
"Fintech companies with banking licenses in the US"
"Cryptocurrency exchanges with regulatory compliance"
"InsurTech startups with Series A funding rounds"
"Payment processors with international coverage"
```

### E-commerce & Retail

```bash
"D2C brands with Shopify Plus implementations"
"Amazon marketplace sellers with private label products"
"Subscription box companies with recurring revenue models"
"Social commerce platforms with influencer partnerships"
```

---

## 🎯 Quick Reference

### Prompt Template

```
[Target Entity] in [Geographic/Domain Scope] with [Specific Criteria] [Optional: Data Type Hints]
```

### Example Application

```
"SaaS companies in Silicon Valley with Series A funding and customer case studies"
```

### Breakdown
- **Target Entity**: SaaS companies
- **Geographic Scope**: Silicon Valley  
- **Specific Criteria**: Series A funding
- **Data Type Hints**: customer case studies

This structure ensures the LLM agents can create focused, effective extraction strategies that deliver high-quality, relevant data.
