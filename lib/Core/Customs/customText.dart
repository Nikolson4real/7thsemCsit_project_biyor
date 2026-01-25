import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class CustomText extends StatelessWidget {
  final String? text;
  final int? maxLength; // NEW: max number of characters
  final TextAlign? textAlign;
  final String? fontFamily;
  final double? fontSize;
  final FontWeight? fontWeight;
  final Color? color;
  final TextDecoration? decoration;
  final Color? decorationColor;
  final TextOverflow? overflow;
  final int? maxLines;
  final bool splitOnSpace;

  const CustomText({
    super.key,
    this.text,
    this.maxLength, // new parameter
    this.textAlign,
    this.fontFamily,
    this.fontSize,
    this.fontWeight,
    this.color,
    this.decoration,
    this.decorationColor,
    this.overflow,
    this.maxLines,
    this.splitOnSpace = false,
  });

  @override
  Widget build(BuildContext context) {
    String displayText = text ?? "";

    // Split first space if needed
    if (splitOnSpace) {
      displayText = displayText.replaceFirst(' ', '\n');
    }

    // Limit max characters if maxLength is provided
    if (maxLength != null && displayText.length > maxLength!) {
      displayText = displayText.substring(0, maxLength!) + '…';
    }

    return Text(
      displayText,
      softWrap: true,
      textAlign: textAlign,
      maxLines: maxLines,
      overflow: overflow ?? TextOverflow.ellipsis,
      style: fontFamily != null
          ? GoogleFonts.getFont(
              fontFamily!,
              textStyle: TextStyle(
                fontSize: fontSize,
                fontWeight: fontWeight,
                color: color ?? Colors.black,
                decoration: decoration,
                decorationColor: decorationColor,
              ),
            )
          : GoogleFonts.roboto(
              textStyle: TextStyle(
                fontSize: fontSize,
                fontWeight: fontWeight,
                color: color ?? Colors.black,
                decoration: decoration,
                decorationColor: decorationColor,
              ),
            ),
    );
  }
}
