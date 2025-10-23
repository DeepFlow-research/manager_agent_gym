# GDPEval Annotation App - Quick Start

## Installation

First, install the curation dependencies:

```bash
cd /Users/charliemasters/Desktop/deepflow/manager_agent_gym
uv sync --group curation
```

This will install:
- **streamlit** - Web app framework
- **PyMuPDF** - PDF rendering and preview
- **python-docx** - Word document text extraction
- **openpyxl** - Excel file reading
- **Pillow** - Image processing

## Running the App

```bash
streamlit run curation/gdpeval/src/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## New Features

### Enhanced File Previews

The app now includes rich preview capabilities for reference files:

#### 📄 **PDF Files**
- Renders first 3 pages inline as images
- Shows page count and navigation
- High-quality rendering (2x zoom)

#### 📊 **Excel Files** (.xlsx, .xls)
- Interactive dataframe viewer
- Multi-sheet support with dropdown selector
- Shows dimensions (rows × columns)

#### 📝 **Word Documents** (.docx)
- Extracts and displays text content
- Shows paragraph count
- Truncates long documents with preview

#### 🖼️ **Images** (.png, .jpg, .gif, etc.)
- Direct inline display
- Full container width

#### 📎 **All Files**
- Clickable `file://` path for opening in default application
- File size display
- No more download buttons cluttering the interface

### Navigation Features

- **Progress tracking**: See how many rubrics generated/annotated
- **Advanced filtering**: By sector, occupation, and status
- **Quick navigation**: Prev/Next buttons to move between tasks
- **Auto-advance**: Automatically moves to next task after saving annotation

## Workflow

1. **Filter tasks**: Use sidebar to filter by sector, occupation, or annotation status
2. **Review task**: Read the prompt and examine reference files with inline previews
3. **Evaluate rubric**: Review the generated evaluation criteria
4. **Annotate**: Provide feedback (Approved/Needs Revision/Rejected)
5. **Navigate**: Use Prev/Next or let it auto-advance to the next task

## Tips

- The first reference file is expanded by default for quick access
- Click the `file://` path to open any file in your default application
- Use the "Not Annotated" filter to see tasks with rubrics that need review
- Your feedback is saved to `data/feedback/feedback.jsonl`

## Keyboard Navigation

- Most browsers support `Tab` to navigate between elements
- `Enter` submits the annotation form
- Use browser back/forward if needed

Enjoy annotating! 🎯
