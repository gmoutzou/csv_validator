# CSV Validator (CVV)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enterprise Data Validation & Quality Assurance Engine
CSV Validator is a powerful, format-agnostic data validation platform built with Python. 
Designed to handle everything from simple integrity checks to complex business logic, it empowers users to define, manage, and execute validation rules at scale.
Whether you are dealing with a few kilobytes or several gigabytes of data, CVV ensures your datasets are accurate, consistent, and ready for production.

## Key Features
### Dynamic Rule Engine
* Agnostic Architecture: No hard-coded rules. The engine is entirely decoupled from the validation logic.
* Hybrid Rule Library: * Remote: Fetch centralized rules from a PostgreSQL database.
* Local: Fallback to a local Python module when offline.
* Logic Operators: Support for complex validation using AND, OR, and XOR logic.
* Cross-Column Validation: Validate dependencies between fields (e.g., If Column A is 'Minor', then Column B must be < 18).
* Rule Templates: Easily import/export rule configurations for recurring validation tasks.

### Performance at Scale
* Parallel Processing Mode: Distribute workloads across multiple Worker Nodes. Data is horizontally sharded into chunks and processed concurrently, with automatic result aggregation.
* Stream Processing Mode: Optimized for GB-scale files. Process data row-by-row to maintain a minimal memory footprint, preventing system crashes on massive datasets.

### Professional Data Utilities
* Custom UI Rule Builder: Write and save custom Python validation functions directly through the interface.
* Outlier Detection: Integrated statistical checks using IQR (Interquartile Range) and Isolation Forest algorithms.
* Data Profiling: Real-time data preview, structure analysis, and value frequency distribution.
* SQL Workbench: Run SQL queries directly against your loaded datasets for ad-hoc data discovery.
* Multi-Format Support: Full compatibility with CSV, XLSX, Fixed Width, XML, and JSON.

## Tech Stack
- Language: Python
- Data Engine: Pandas, Numpy
- Machine Learning: Scikit-learn (for Isolation Forest)
- Database: PostgreSQL
- Architecture: Distributed Worker/Client model

## Workflow
1. Ingest: Load your data file (CSV, JSON, etc.).
2. Map: Use the Rule Panel to map columns to specific validation rules.
3. Execute: Click "Fire All Rules" to trigger the engine.
4. Review: Analyze the detailed error report (Mapping Column/Row/Invalid Value).
5. Export: Save your cleaned data or validation logs in multiple formats.

## Developer
Georgios Mountzouris 📧 gmountzouris@efka.gov.gr

## License
This project is licensed under the MIT License - see the LICENSE file for details.
