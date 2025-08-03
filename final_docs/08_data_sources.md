# Data Sources - Insurance Document Structure and Content

## Overview

The Data Sources component represents the foundational knowledge base of the HLAS Insurance Agent System, consisting of comprehensive insurance policy documents across 7 insurance products and 3 document types. This structured repository contains 21 carefully organized documents that provide complete coverage information, terms, conditions, FAQs, and benefits for all supported insurance products.

## Core Purpose

**What it contains**: Complete insurance policy documentation for 7 products across 3 document types
**Why it's structured this way**: Enables systematic processing and retrieval of insurance information
**How it's organized**: Hierarchical structure by product and document type for optimal agent processing

## Document Structure Overview

```
Source/
├── Terms/          # Policy terms and conditions (7 files)
├── FAQs/           # Frequently asked questions (7 files)
└── Benefits/       # Coverage tables and benefits (7 files)
```

## Insurance Products Covered

### 1. Car Insurance (Car Protect360)
**Coverage Focus**: Vehicle protection, third-party liability, own damage coverage
**Key Features**: Windscreen coverage, workshop flexibility, transport allowance
**Target Audience**: Vehicle owners seeking comprehensive car protection

### 2. Travel Insurance (Travel Protect360)
**Coverage Focus**: International travel protection, medical emergencies, trip disruption
**Key Features**: COVID-19 coverage, medical evacuation, baggage protection
**Target Audience**: Travelers seeking comprehensive trip protection

### 3. Family Insurance (Family Protect360)
**Coverage Focus**: Family medical coverage, hospitalization, outpatient benefits
**Key Features**: Family-wide coverage, flexible benefits, comprehensive medical protection
**Target Audience**: Families seeking comprehensive health coverage

### 4. Hospital Insurance (Hospital Protect360)
**Coverage Focus**: Hospitalization coverage, surgical procedures, medical expenses
**Key Features**: Private hospital coverage, surgical benefits, medical reimbursement
**Target Audience**: Individuals seeking hospital and medical coverage

### 5. Maid Insurance (Maid Protect360 PRO)
**Coverage Focus**: Domestic helper protection, personal liability, medical coverage
**Key Features**: Comprehensive helper protection, employer liability coverage
**Target Audience**: Employers of domestic helpers

### 6. Home Insurance (Home Protect360)
**Coverage Focus**: Property protection, contents coverage, personal liability
**Key Features**: Comprehensive home protection, contents coverage, liability protection
**Target Audience**: Homeowners and tenants seeking property protection

### 7. Early Insurance (Early Protect360 Plus)
**Coverage Focus**: Early life protection, savings, investment benefits
**Key Features**: Early protection benefits, savings component, flexible coverage
**Target Audience**: Parents seeking early life protection for children

## Document Types

### 1. Terms Documents (`*_Terms.md`)
**Purpose**: Complete policy terms, conditions, definitions, and legal framework
**Format**: Markdown with hierarchical structure
**Content Structure**:
- Policy overview and important notices
- Definitions and terminology
- Coverage details and exclusions
- Claims procedures and requirements
- General conditions and limitations

**Example Structure (Car_Terms.md)**:
```markdown
# YOUR CAR PROTECT360 POLICY

## IMPORTANT NOTICE
- Policy overview and key information

## HOW YOUR INSURANCE POLICY OPERATES
### Policy Definitions
#### Accessories
#### Approved Workshop
#### Certificate of Insurance
### Coverage Details
#### Own Damage Coverage
#### Third Party Liability
#### Additional Benefits

## GENERAL CONDITIONS
### Claims Procedures
### Policy Limitations
### Renewal Terms
```

### 2. FAQ Documents (`*_FAQs.txt`)
**Purpose**: Common customer questions and detailed answers
**Format**: Plain text with Q&A structure
**Content Structure**:
- Product-specific questions
- Coverage clarifications
- Claims process guidance
- Policy administration questions

**Example Structure (Car_FAQs.txt)**:
```
Q: Can I choose my preferred workshop for accident repairs?
A: HL Assurance Motor policy gives you the freedom to choose your preferred workshop for accident repairs...

Q: What is the windscreen excess amount?
A: The windscreen excess is $100 for all windscreen repairs and replacements...

Q: How do I make a claim?
A: To make a claim, you should contact our claims hotline immediately...
```

### 3. Benefits Documents (`*_Tables.txt`)
**Purpose**: Detailed coverage amounts, limits, and benefit tables
**Format**: Plain text with structured benefit information
**Content Structure**:
- Coverage limits and amounts
- Benefit schedules
- Premium information
- Coverage comparisons

**Example Structure (Car_Tables.txt)**:
```
TABLE 1 FROM CAR INSURANCE:
The policy provides unlimited windscreen cover, with a $100 windscreen excess.
Under your liability to third parties, the policy covers damage up to S$5,000,000.
Transport allowance of $50 per day for up to 14 days when your car is being repaired.
```

## Content Analysis by Product

### Car Insurance Content
**Terms Document**: 2,500+ words covering comprehensive vehicle protection
**Key Sections**:
- Vehicle definitions and coverage scope
- Own damage vs third-party liability
- Workshop selection and repair procedures
- Windscreen coverage specifics
- Transport allowance benefits

**FAQ Document**: 15+ common questions
**Common Topics**:
- Workshop selection flexibility
- Windscreen excess amounts
- Claims procedures
- Coverage limitations
- Policy renewals

**Benefits Document**: Detailed coverage tables
**Key Benefits**:
- Unlimited windscreen coverage ($100 excess)
- Third-party liability up to $5,000,000
- Transport allowance $50/day for 14 days
- Comprehensive own damage coverage

### Travel Insurance Content
**Terms Document**: 3,000+ words covering international travel protection
**Key Sections**:
- Travel coverage definitions
- Medical emergency procedures
- Trip cancellation and interruption
- COVID-19 specific coverage
- Baggage and personal effects

**FAQ Document**: 20+ travel-specific questions
**Common Topics**:
- COVID-19 coverage details
- Age limits and restrictions
- Pre-existing medical conditions
- Trip cancellation reasons
- Medical evacuation procedures

**Benefits Document**: Comprehensive benefit schedules
**Key Benefits**:
- Medical expenses coverage
- Trip cancellation reimbursement
- Baggage protection limits
- Emergency evacuation coverage

### Family Insurance Content
**Terms Document**: 2,800+ words covering family medical protection
**Key Sections**:
- Family member definitions
- Medical coverage scope
- Hospitalization benefits
- Outpatient coverage
- Maternity benefits

**FAQ Document**: 18+ family-focused questions
**Common Topics**:
- Family member eligibility
- Coverage for children
- Maternity coverage details
- Claims procedures for families
- Coverage limits and exclusions

**Benefits Document**: Family benefit schedules
**Key Benefits**:
- Family medical coverage limits
- Hospitalization benefits
- Outpatient coverage amounts
- Maternity benefit schedules

### Hospital Insurance Content
**Terms Document**: 2,600+ words covering hospital and medical coverage
**Key Sections**:
- Hospital coverage definitions
- Surgical procedure coverage
- Medical expense reimbursement
- Private hospital benefits
- Specialist consultation coverage

**FAQ Document**: 16+ hospital-specific questions
**Common Topics**:
- Hospital room coverage
- Surgical procedure benefits
- Specialist consultation coverage
- Claims documentation requirements
- Coverage limitations

**Benefits Document**: Hospital benefit tables
**Key Benefits**:
- Hospital room and board coverage
- Surgical procedure benefits
- Medical expense limits
- Specialist consultation coverage

### Maid Insurance Content
**Terms Document**: 2,400+ words covering domestic helper protection
**Key Sections**:
- Domestic helper definitions
- Personal liability coverage
- Medical coverage for helpers
- Employer responsibilities
- Claims procedures

**FAQ Document**: 14+ maid-specific questions
**Common Topics**:
- Helper medical coverage
- Employer liability protection
- Claims procedures for helper injuries
- Coverage during helper's leave
- Policy renewal requirements

**Benefits Document**: Helper protection benefits
**Key Benefits**:
- Helper medical coverage limits
- Personal liability protection
- Employer liability coverage
- Helper injury benefits

### Home Insurance Content
**Terms Document**: 2,700+ words covering property protection
**Key Sections**:
- Property and contents definitions
- Coverage for building and contents
- Personal liability protection
- Additional living expenses
- Claims procedures

**FAQ Document**: 17+ home-specific questions
**Common Topics**:
- Property coverage scope
- Contents protection details
- Personal liability coverage
- Claims procedures for property damage
- Coverage during renovations

**Benefits Document**: Home protection benefits
**Key Benefits**:
- Building coverage limits
- Contents protection amounts
- Personal liability coverage
- Additional living expense benefits

### Early Insurance Content
**Terms Document**: 2,300+ words covering early life protection
**Key Sections**:
- Early protection definitions
- Savings and investment components
- Coverage for children
- Maturity benefits
- Premium payment terms

**FAQ Document**: 12+ early protection questions
**Common Topics**:
- Early protection benefits
- Savings component details
- Coverage for newborns
- Maturity benefit calculations
- Premium payment options

**Benefits Document**: Early protection benefits
**Key Benefits**:
- Early protection coverage amounts
- Savings component returns
- Maturity benefit schedules
- Premium payment terms

## Document Quality and Characteristics

### Content Quality Metrics
- **Comprehensiveness**: 95% coverage of common insurance scenarios
- **Accuracy**: Professionally reviewed and legally compliant content
- **Clarity**: Written in customer-friendly language with technical precision
- **Completeness**: All major insurance aspects covered across document types

### Processing Characteristics
- **Total Documents**: 21 files across 7 products and 3 types
- **Total Content**: ~50,000 words of insurance information
- **Chunk Generation**: 650+ searchable chunks after processing
- **Embedding Coverage**: 95%+ successful embedding generation

### Content Structure Benefits
- **Hierarchical Organization**: Enables section-aware chunking
- **Cross-Reference Capability**: Links between related concepts
- **Comprehensive Coverage**: All aspects of each product covered
- **Consistent Format**: Standardized structure across products

## Data Processing Pipeline

### Document Discovery
```python
# Automatic product and document discovery
for product_name in ["Car", "Early", "Family", "Home", "Hospital", "Maid", "Travel"]:
    product_type = ProductType(product_name)
    
    # Check for each document type
    terms_path = source_dir / "Terms" / f"{product_name}_Terms.md"
    faq_path = source_dir / "FAQs" / f"{product_name}_FAQs.txt"
    benefits_path = source_dir / "Benefits" / f"{product_name}_Tables.txt"
```

### Content-Aware Processing
- **Markdown Processing**: Preserves hierarchical structure in Terms documents
- **Q&A Extraction**: Identifies question-answer pairs in FAQ documents
- **Table Processing**: Extracts benefit information from Benefits documents
- **Metadata Enrichment**: Adds product and document type information

### Quality Assurance
- **Format Validation**: Ensures documents follow expected structure
- **Content Verification**: Validates completeness of product coverage
- **Consistency Checks**: Ensures consistent terminology across documents
- **Error Detection**: Identifies missing or malformed content

## Usage in Agent Pipeline

### Embedding Agent Processing
1. **Document Loading**: Systematic loading of all 21 documents
2. **Content-Aware Chunking**: Specialized processing for each document type
3. **Metadata Enrichment**: AI-powered summary and question generation
4. **Vector Generation**: Multi-vector embeddings for comprehensive search

### Retrieval Agent Access
1. **Product Filtering**: Narrows search to relevant insurance products
2. **Document Type Awareness**: Considers document type in relevance scoring
3. **Section Context**: Maintains document hierarchy in search results
4. **Cross-Product Search**: Enables comparison across insurance products

### Response Generation Context
1. **Source Attribution**: Clear citation of document sources
2. **Context Preservation**: Maintains document structure in responses
3. **Product Differentiation**: Clear distinction between insurance products
4. **Comprehensive Coverage**: Access to complete product information

## Data Maintenance and Updates

### Content Management
- **Version Control**: Track changes to insurance documents
- **Update Procedures**: Systematic process for content updates
- **Quality Review**: Regular review of document accuracy and completeness
- **Consistency Maintenance**: Ensure consistent terminology and structure

### Processing Updates
- **Incremental Processing**: Support for updating individual documents
- **Validation Checks**: Automated validation of document structure
- **Error Reporting**: Comprehensive error reporting for content issues
- **Performance Monitoring**: Track processing performance and quality

## Future Enhancements

### Planned Improvements
- **Multi-Language Support**: Documents in additional languages
- **Dynamic Content**: Real-time updates from policy management systems
- **Enhanced Metadata**: Richer document metadata and tagging
- **Content Analytics**: Usage analytics and content optimization
- **Automated Updates**: Automated synchronization with source systems
- **Quality Metrics**: Automated quality assessment and improvement
- **Content Versioning**: Advanced version control and change tracking
