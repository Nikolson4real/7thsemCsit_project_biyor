import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:pdfx/pdfx.dart';

class BiyorRuleBook extends StatefulWidget {
  const BiyorRuleBook({super.key});

  @override
  State<BiyorRuleBook> createState() => _BiyorRuleBookState();
}

class _BiyorRuleBookState extends State<BiyorRuleBook> {
  late PdfControllerPinch _pdfController;
  bool _isLoading = true;
  String? _errorMessage;
  int _totalPages = 0;
  int _currentPage = 1;

  @override
  void initState() {
    super.initState();
    _loadPdf();
  }

  /// Load PDF from assets
  Future<void> _loadPdf() async {
    try {
      _pdfController = PdfControllerPinch(
        document: PdfDocument.openAsset('assets/pdf/gamerule.pdf'),
      );
      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Failed to load PDF: $e';
      });
    }
  }

  @override
  void dispose() {
    _pdfController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(65),
        child: ClipRRect(
          borderRadius: const BorderRadius.only(
            bottomLeft: Radius.circular(20),
            bottomRight: Radius.circular(20),
          ),
          child: AppBar(
            centerTitle: true,
            title: const CustomText(
              text: 'DandiBiyo Rule Book',
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: whiteColor,
            ),
            backgroundColor: Colors.transparent,
            elevation: 0,
            flexibleSpace: Container(
              decoration: const BoxDecoration(
                image: DecorationImage(
                  image: AssetImage("assets/images/biyorbgi.jpg"),
                  fit: BoxFit.cover,
                ),
              ),
            ),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: whiteColor, size: 30),
              onPressed: () => Navigator.pop(context),
            ),
          ),
        ),
      ),
      body: Stack(
        children: [
          _buildBody(),
          // Floating page navigation overlay
          if (!_isLoading && _errorMessage == null && _totalPages > 0)
            Positioned(
              left: 0,
              right: 0,
              bottom: 16,
              child: SafeArea(
                child: Center(
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Previous page button
                        IconButton(
                          icon: Icon(
                            Icons.arrow_back_ios,
                            color: _currentPage > 1
                                ? Colors.white
                                : Colors.white.withOpacity(0.3),
                            size: 20,
                          ),
                          onPressed: _currentPage > 1
                              ? () => _pdfController.previousPage(
                                    duration: const Duration(milliseconds: 300),
                                    curve: Curves.easeInOut,
                                  )
                              : null,
                        ),
                        // Page indicator
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: CustomText(
                            text: '$_currentPage / $_totalPages',
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                        // Next page button
                        IconButton(
                          icon: Icon(
                            Icons.arrow_forward_ios,
                            color: _currentPage < _totalPages
                                ? Colors.white
                                : Colors.white.withOpacity(0.3),
                            size: 20,
                          ),
                          onPressed: _currentPage < _totalPages
                              ? () => _pdfController.nextPage(
                                    duration: const Duration(milliseconds: 300),
                                    curve: Curves.easeInOut,
                                  )
                              : null,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    // Loading state
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(woodBrown),
            ),
            const SizedBox(height: 16),
            const CustomText(
              text: 'Loading Rule Book...',
              fontSize: 16,
              color: woodBrown,
            ),
          ],
        ),
      );
    }

    // Error state
    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red[400]),
              const SizedBox(height: 16),
              CustomText(
                text: 'Could not load Rule Book',
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.red[700]!,
              ),
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[600], fontSize: 14),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () {
                  setState(() {
                    _isLoading = true;
                    _errorMessage = null;
                  });
                  _loadPdf();
                },
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: woodBrown,
                  foregroundColor: whiteColor,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // PDF view using pdfx
    return PdfViewPinch(
      controller: _pdfController,
      onDocumentLoaded: (document) {
        setState(() {
          _totalPages = document.pagesCount;
        });
      },
      onPageChanged: (page) {
        setState(() {
          _currentPage = page;
        });
      },
      onDocumentError: (error) {
        setState(() {
          _errorMessage = error.toString();
        });
      },
      builders: PdfViewPinchBuilders<DefaultBuilderOptions>(
        options: const DefaultBuilderOptions(),
        documentLoaderBuilder: (_) => Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(woodBrown),
          ),
        ),
        pageLoaderBuilder: (_) => Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(woodBrown),
          ),
        ),
        errorBuilder: (_, error) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red[400]),
              const SizedBox(height: 16),
              Text(
                'Error loading page',
                style: TextStyle(color: Colors.red[700], fontSize: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
