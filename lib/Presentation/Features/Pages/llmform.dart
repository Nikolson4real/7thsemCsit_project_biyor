import 'package:biyoar/Core/Customs/customAlertDialog.dart';
import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Core/Customs/customTextForm.dart';
import 'package:biyoar/Core/StateManagement/biyorEvents.dart';
import 'package:biyoar/Core/StateManagement/gameRulesBloc.dart';
import 'package:biyoar/Presentation/Features/Dashboard/userdash2.dart';
import 'package:biyoar/Presentation/Features/Pages/rulesCard.dart';
import 'package:biyoar/test/woodenChickenObject.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class LLMForm extends StatefulWidget {
  const LLMForm({super.key});

  @override
  State<LLMForm> createState() => _LLMFormState();
}

class _LLMFormState extends State<LLMForm> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController dandilengthController = TextEditingController();
  final TextEditingController biyoLengthController = TextEditingController();
  final TextEditingController biyoDiameterController = TextEditingController();
  final TextEditingController fieldLengthController = TextEditingController();
  final TextEditingController fieldWidthController = TextEditingController();
  final TextEditingController numPlayersController = TextEditingController();

  final List<String> surfaceTypes = [
    'grass',
    'dirt',
    'sand',
    'concrete',
    'other',
  ];
  String? selectedSurface;

  void clearAllFields() {
    setState(() {
      dandilengthController.clear();
      biyoLengthController.clear();
      biyoDiameterController.clear();
      fieldLengthController.clear();
      fieldWidthController.clear();
      numPlayersController.clear();
      selectedSurface = null;
    });
    setState(() {
      _formKey.currentState?.validate();
    });
  }

  bool isFormCompletelyEmpty() {
    return dandilengthController.text.trim().isEmpty &&
        biyoLengthController.text.trim().isEmpty &&
        biyoDiameterController.text.trim().isEmpty &&
        fieldLengthController.text.trim().isEmpty &&
        fieldWidthController.text.trim().isEmpty &&
        numPlayersController.text.trim().isEmpty &&
        selectedSurface == null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
              image: DecorationImage(
            image: AssetImage('assets/images/biyorbgi.jpg'), // From assets
            fit: BoxFit.cover, // This makes image cover entire container
            colorFilter: ColorFilter.mode(
              Colors.black.withOpacity(0.3), // Optional: Add overlay color
              BlendMode.darken,
            ),
          )),
          child: SingleChildScrollView(
            scrollDirection: Axis.vertical,
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    height: 50,
                  ),
                  Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: IconButton(
                      color: whiteColor,
                      onPressed: () {
                        Navigator.pop(context);
                      },
                      icon: Icon(Icons.arrow_back),
                      iconSize: 30,
                    ),
                  ),
                  Center(
                    child: CustomText(
                      text: "Fill up the form for better experience.",
                      color: whiteColor,
                    ),
                  ),
                  SizedBox(
                    height: 10,
                  ),
                  CustomTextForm(
                      keyboardType: TextInputType.number,
                      hintText: "enter the length of dandi (cm)",
                      validator: (value) {
                        if (value == null || value.isEmpty)
                          return null; // optional
                        final num? v = num.tryParse(value);
                        if (v == null) return 'Enter a valid number';
                        if (v < 1 || v > 200)
                          return 'Dandi length must be 1–200 cm';
                        return null;
                      },
                      controller: dandilengthController),
                  SizedBox(
                    height: 10,
                  ),
                  CustomTextForm(
                    keyboardType: TextInputType.number,
                    hintText: "enter the length of biyo (cm)",
                    validator: (value) {
                      if (value == null || value.isEmpty) return null;
                      final num? v = num.tryParse(value);
                      if (v == null) return 'Enter a valid number';
                      if (v < 1 || v > 50) return 'Biyo length must be 1–50 cm';
                      return null;
                    },
                    controller: biyoLengthController,
                  ),
                  SizedBox(
                    height: 10,
                  ),
                  // CustomTextForm(
                  //   keyboardType: TextInputType.number,
                  //   hintText: "enter the diameter of biyo (cm)",
                  //   validator: (value) {
                  //     if (value == null || value.isEmpty) return null;
                  //     final num? v = num.tryParse(value);
                  //     if (v == null) return 'Enter a valid number';
                  //     if (v < 1 || v > 10)
                  //       return 'Biyo diameter must be 1–10 cm';
                  //     return null;
                  //   },
                  //   controller: biyoDiameterController,
                  // ),
                  // SizedBox(
                  //   height: 10,
                  // ),
                  CustomTextForm(
                    keyboardType: TextInputType.number,
                    hintText: "enter the length of field (m)",
                    validator: (value) {
                      if (value == null || value.isEmpty) return null;
                      final num? v = num.tryParse(value);
                      if (v == null) return 'Enter a valid number';
                      if (v < 1 || v > 100)
                        return 'Field length must be 1–100 m';
                      return null;
                    },
                    controller: fieldLengthController,
                  ),
                  SizedBox(
                    height: 10,
                  ),
                  CustomTextForm(
                    keyboardType: TextInputType.number,
                    hintText: "enter the width of field (m)",
                    validator: (value) {
                      if (value == null || value.isEmpty) return null;
                      final num? v = num.tryParse(value);
                      if (v == null) return 'Enter a valid number';
                      if (v < 1 || v > 100)
                        return 'Field width must be 1–100 m';
                      return null;
                    },
                    controller: fieldWidthController,
                  ),
                  SizedBox(
                    height: 65,
                    width: 500,
                    child: Padding(
                      padding:
                          const EdgeInsets.only(left: 30, right: 25, top: 5),
                      child: DropdownButtonFormField<String>(
                        value: selectedSurface,
                        decoration: InputDecoration(
                          labelText: 'surface type',
                          labelStyle: TextStyle(color: greyColor, fontSize: 16),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide:
                                BorderSide(color: borderColor, width: 2),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide:
                                BorderSide(color: borderColor, width: 2),
                          ),
                        ),
                        items: surfaceTypes.map((surface) {
                          return DropdownMenuItem(
                            value: surface,
                            child: Text(surface.toLowerCase()),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedSurface = value;
                          });
                        },
                        validator: (value) {
                          return null;
                        },
                      ),
                    ),
                  ),
                  SizedBox(
                    height: 10,
                  ),

                  SizedBox(
                    height: 10,
                  ),
                  CustomTextForm(
                    keyboardType: TextInputType.number,
                    hintText: "enter the number of players",
                    validator: (value) {
                      // Allow empty value
                      if (value == null || value.isEmpty) {
                        return null; // optional, no error
                      }

                      // Validate if user enters something
                      final int? v = int.tryParse(value);
                      if (v == null) return 'Enter a valid number';
                      if (v < 1) return 'At least 1 player required';
                      return null;
                    },
                    controller: numPlayersController,
                  ),
                  SizedBox(
                    height: 10,
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(
                        height: 50,
                        width: 150,
                        child: CustomButton(
                          //color: woodBrown.withOpacity(0.45),
                          color: whiteColor,
                          borderColor: borderColor,
                          fontsize: 18,
                          onPressed: () {
                            // // ❌ SOME FILLED BUT INVALID → SHOW ERRORS
                            // if (!_formKey.currentState!.validate()) {
                            //   return;
                            // }
                            // Navigator.push(
                            //   context,
                            //   MaterialPageRoute(
                            //       builder: (_) => RulesCardBiyor()),
                            // );
                            if (!_formKey.currentState!.validate()) {
                              return;
                            }

                            // 🔥 ADDED: API trigger via Bloc
                            context.read<GameRulesBloc>().add(
                                  FetchGameRules(
                                    biyoLength: int.tryParse(
                                            biyoLengthController.text) ??
                                        10,
                                    dandiLength: int.tryParse(
                                            dandilengthController.text) ??
                                        90,
                                    fieldLength: int.tryParse(
                                            fieldLengthController.text) ??
                                        80,
                                    fieldWidth: int.tryParse(
                                            fieldWidthController.text) ??
                                        70,
                                    surfaceType: selectedSurface ?? "grass",
                                    players: int.tryParse(
                                            numPlayersController.text) ??
                                        4,
                                  ),
                                );

                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => RulesCardBiyor(),
                              ),
                            );
                          },
                          child: CustomText(
                            text: "Submit",
                            //
                            // color: Colors.white,
                            color: greenColor,
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      SizedBox(
                        height: 50,
                        width: 150,
                        child: CustomButton(
                            //color: woodBrown.withOpacity(0.45),
                            color: whiteColor,
                            borderColor: borderColor,
                            onPressed: () {
                              clearAllFields();
                            },
                            child: CustomText(
                              text: "Clear",
                              color: redColor,
                              fontSize: 18,
                              fontWeight: FontWeight.w500,
                            )),
                      ),
                    ],
                  )
                ],
              ),
            ),
          )),
    );
  }
}
