import Foundation
import PDFKit
import AppKit

if CommandLine.arguments.count < 4 {
    fputs("usage: render_pdf_page.swift <pdf_path> <page_number> <output_png>\n", stderr)
    exit(2)
}

let pdfPath = CommandLine.arguments[1]
let pageNumber = Int(CommandLine.arguments[2]) ?? 0
let outputPath = CommandLine.arguments[3]

guard pageNumber > 0 else {
    fputs("page_number must be 1-based\n", stderr)
    exit(2)
}

let pdfURL = URL(fileURLWithPath: pdfPath)
guard let document = PDFDocument(url: pdfURL) else {
    fputs("failed to open pdf\n", stderr)
    exit(1)
}

guard let page = document.page(at: pageNumber - 1) else {
    fputs("page out of range\n", stderr)
    exit(1)
}

let image = page.thumbnail(of: NSSize(width: 1400, height: 1800), for: .mediaBox)
guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let png = bitmap.representation(using: .png, properties: [:]) else {
    fputs("failed to encode png\n", stderr)
    exit(1)
}

do {
    try png.write(to: URL(fileURLWithPath: outputPath))
    print(outputPath)
} catch {
    fputs("failed to write png: \(error)\n", stderr)
    exit(1)
}
