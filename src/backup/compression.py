import gzip
import bz2
import lzma
from pathlib import Path
from typing import Optional

class CompressionManager:

    def __init__(self, compression_type: str = 'gzip'):
        self.compression_type = compression_type.lower()

        self.compressors = {
            'gzip': self._compress_gzip,
            'bz2': self._compress_bz2,
            'xz': self._compress_xz,
            'none': self._no_compression
        }

        self.decompressors = {
            'gzip': self._decompress_gzip,
            'bz2': self._decompress_bz2,
            'xz': self._decompress_xz,
            'none': self._no_decompression
        }

        if self.compression_type not in self.compressors:
            raise ValueError(f"Tipo de compressão não suportado: {compression_type}")

    def compress(self, input_path: str, output_path: Optional[str] = None) -> str:
        if not output_path:
            extensions = {
                'gzip': '.gz',
                'bz2': '.bz2',
                'xz': '.xz',
                'none': ''
            }
            output_path = f"{input_path}{extensions[self.compression_type]}"

        return self.compressors[self.compression_type](input_path, output_path)

    def decompress(self, input_path: str, output_path: str) -> str:
        compression_type = self._detect_compression(input_path)
        return self.decompressors[compression_type](input_path, output_path)

    def _compress_gzip(self, input_path: str, output_path: str) -> str:
        with open(input_paht, 'rb') as f_in:
            with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
                f_out.writelines(f_in)
        return output_path

    def _compress_bz2(self, input_path: str, output_path: str) -> str:
        with open(input_path, 'rb') as f_in:
            with bz2.open(output_path, 'wb', compresslevel=9) as f_out:
                f_out.writelines(f_in)
        return output_path

    def _compress_xz(self, input_path: str, output_path: str) -> str:
        with open(input_path, 'rb') as f_in:
            with lzma.open(output_path, 'wb', preset=6) as f_out:
                f_out.writelines(f_in)
        return output_path

    def _no_compression(self, input_path: str, output_path: str) -> str:
        return input_path

    def _decompress_gzip(self, input_path: str, output_path: str) -> str:
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.writelines(f_in)
        return output_path

    def _decompress_bz2(self, input_path: str, output_path: str) -> str:
        with bz2.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.writelines(f_in)
        return output_path
    
    def _decompress_xz(self, input_path: str, output_path: str) -> str:
        with lzma.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.writelines(f_in)
        return output_path

    def _no_decompression(self, input_path: str, output_path: str) -> str:
        return input_path

    def _detect_compression(self, file_path: str) -> str:
        path = Path(file_path)

        if path.suffix == '.gz':
            return 'gzip'
        elif path.suffix == '.bz2':
            return 'bz2'
        elif path.suffix == '.xz':
            return 'xz'
        else:
            return 'none'
