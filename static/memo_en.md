# 📓 Laser Engraving Tips & Tricks

## Basic Laser Engraving Principles

- **Speed (mm/s):**
    - Higher speed = lighter mark.
    - Too fast may not engrave properly.
    - Typical range: 20-100 mm/s.
- **Power (%):**
    - Higher power = deeper mark.
    - Too much power may cause burns or material damage.
    - Typical range: 30-100%.
- **Focal Distance (mm):**
    - The distance between laser head and material surface.
    - Must be precise for sharp/contrasted lines.
    - Usually 0-5mm below lens.

## Job Workflow

1. **Select the correct machine:** Choose the appropriate laser.
2. **Select correct material:** Choose the material type and thickness for your project.
3. **Place your engraving material:** Position material on the cutting bed. Ensure it is flat and secured.
4. **Delimit the engraving zone:** Mark the area where you want to engrave using the software's boundary tool.
5. **Position on the correct focal distance:** Use the autofocus feature.
6. **Place your numeric file in the zone:** Load your design file and position it within the marked area.
7. **Check laser config for each color line:** Verify that all colored lines have correct speed/power settings assigned.
8. **Burn:** Start the engraving process and monitor progress.

## Colors & Laser Configuration

| Color     | Meaning   | Description                                                |
|-----------|-----------|------------------------------------------------------------|
| ⬛ Black   | *score*   | Cut partially through material, creating nice sharp lines. |
| 🟥 Red    | *cut*     | Cut completely through material.                           |
| 🟩 Green  | *engrave* | Engrave surface without cutting through.                   |
| 🟪 Purple | Image     | Raster image engraving with photo-like results.            |
| ⬜ Grey    | Technical | Ignored/not processed by laser.                            |

### ⚠️ Important Reminder

Ensure all lines of the same color are configured with identical laser settings. Select a color line and re-apply its
configuration to all matching colors.

## Global Tips

- **Use English version of application:** The French translation is not well maintained.
- **Test on scrap material first:** Always test settings on spare material before running production jobs.
- **Keep lens clean:** A dirty lens reduces power and causes poor focus. Clean regularly.
- **Use proper ventilation:** Always use air assist and exhaust when cutting/engraving.
- **Check bed alignment:** Misaligned bed causes uneven burns. Use autofocus before each job.
- **Record successful settings:** Keep notes of speed/power for different materials for future reference.
