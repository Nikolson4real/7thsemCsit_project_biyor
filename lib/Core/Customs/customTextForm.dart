import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class CustomTextForm extends StatelessWidget {
  String? hintText, initialValue;
  double? fontSize;
  Function(String)? onChanged;
  TextInputType? keyboardType;
  String? Function(String?)? validator;
  bool obscureText;
  Widget? prefixIcon;
  Widget? suffixIcon;
  List<TextInputFormatter>? inputFormatters;
  int? maxLength;
  Widget? label;
  TextEditingController? controller;
  bool? enabled;
  String? fontFamily;
  TextStyle? hintStyle;
  double? hintFontSize;
  BorderSide? bColor;
  bool readOnly;
  final Color cursorColor; // Add this

  CustomTextForm({
    super.key,
    this.onChanged,
    this.hintText,
    this.hintStyle,
    this.hintFontSize,
    this.validator,
    this.fontSize,
    this.keyboardType,
    this.inputFormatters,
    this.obscureText = false,
    this.prefixIcon,
    this.suffixIcon,
    this.label,
    this.maxLength,
    this.controller,
    this.enabled,
    this.initialValue,
    this.fontFamily,
    this.bColor,
    this.readOnly = false,
    this.cursorColor = whiteColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 30, right: 25, top: 5),
      child: Container(
        child: TextFormField(
          cursorColor: Colors.white,
          controller: controller, // use controller only if provided
          initialValue: controller == null
              ? initialValue
              : null, // only use initialValue when controller is not used
          enabled: enabled,
          autovalidateMode: AutovalidateMode.onUserInteraction,
          maxLength: maxLength,
          decoration: InputDecoration(
            enabledBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12.0)),
              borderSide: BorderSide(
                width: 2,
                //color: Color.fromARGB(255, 207, 198, 198),
                color: borderColor,
              ),
            ),
            focusedBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12.0)),
              borderSide: BorderSide(
                width: 2,
                // color: Color.fromARGB(255, 207, 198, 198),
                color: borderColor,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12.0)),
              borderSide: BorderSide(
                color: Color.fromARGB(255, 207, 198, 198),
                width: 2,
              ), // Border when error occurs
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12.0)),
              borderSide: BorderSide(
                color: Color.fromARGB(255, 207, 198, 198),
                width: 2,
              ), // Border when focused with error
            ),
            contentPadding: const EdgeInsets.symmetric(
              vertical: 10,
              horizontal: 7.0,
            ),
            prefixIcon: prefixIcon,
            label: label,
            hintText: hintText,
            hintStyle: TextStyle(
              fontFamily: "Lato",
              fontSize: hintFontSize,
              color: Colors.grey,
              fontWeight: FontWeight.w300,
            ),
            suffixIcon: suffixIcon,
            // fillColor: const Color(0xffFFFFFF),
            fillColor: Colors.transparent,

            filled: true,
          ),
          style: TextStyle(
              fontFamily: fontFamily ?? '',
              fontSize: fontSize,
              color: whiteColor),

          validator: validator,
          obscureText: obscureText,
          onChanged: onChanged,
          keyboardType: keyboardType,
          readOnly: readOnly,
        ),
      ),
    );
  }
}
