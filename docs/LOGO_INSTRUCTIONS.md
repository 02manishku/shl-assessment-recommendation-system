# 📸 SHL Logo Integration Instructions

## Overview

The Streamlit app now includes SHL logo support with automatic fallback options. The logo will be displayed in:
- Main header (left side, 150px width)
- Sidebar (top, 120px width)

## Logo Display Priority

The app tries to load the logo in this order:

1. **Local file**: `shl_logo.png` (in project root)
2. **Assets folder**: `assets/shl_logo.png`
3. **Official SHL logo URL**: `https://www.shl.com/wp-content/uploads/2020/06/SHL_Logo_RGB_2020.png`
4. **Alternative SVG**: `https://www.shl.com/static/images/shl-logo.svg`
5. **Fallback**: Text-based "SHL" logo with styling

## Adding Your Own Logo

### Option 1: Local File (Recommended)

1. Download the SHL logo image (PNG format recommended)
2. Save it as `shl_logo.png` in the project root directory
3. The app will automatically use it

### Option 2: Assets Folder

1. Create an `assets` folder in the project root
2. Save the logo as `assets/shl_logo.png`
3. The app will automatically use it

### Option 3: Custom URL

Edit `app.py` and modify the `display_shl_logo()` function to add your custom logo URL:

```python
logo_sources = [
    ("shl_logo.png", "local"),
    ("assets/shl_logo.png", "local"),
    ("YOUR_CUSTOM_URL_HERE", "url"),  # Add your URL
    # ... existing sources
]
```

## Logo Specifications

- **Format**: PNG, SVG, or JPG
- **Recommended size**: 300x100px or similar aspect ratio
- **Transparent background**: Preferred for better integration
- **File size**: Keep under 500KB for faster loading

## Testing

To test the logo:

1. Run the Streamlit app: `streamlit run app.py`
2. Check the header area - logo should appear on the left
3. Check the sidebar - logo should appear at the top
4. If logo doesn't load, the fallback text logo will be displayed

## Troubleshooting

### Logo not displaying?

1. Check if the file exists in the correct location
2. Verify file permissions
3. Check file format (PNG/SVG/JPG)
4. Try using the official SHL logo URL
5. Check browser console for errors

### Logo too large/small?

Edit the `width` parameter in `display_shl_logo()` calls:
- Header: `display_shl_logo(width=150, container=st)`
- Sidebar: `display_shl_logo(width=120, container=st.sidebar)`

### Want to hide the logo?

Comment out the `display_shl_logo()` calls in `main()` function.

## Notes

- The app uses graceful fallback - if logo loading fails, it displays a styled text logo
- Logo is cached by Streamlit for performance
- Supports both local files and remote URLs
- Automatically handles errors without breaking the app

