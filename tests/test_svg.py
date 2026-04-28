from __future__ import annotations

import inspect
import re
import sys
pass
import hashlib
from pathlib import Path

import pytest
from lxml import etree

try:
    import boxes
except ImportError:
    sys.path.append(Path(__file__).resolve().parent.parent.__str__())
    import boxes

import boxes.generators


import yaml


class TestSVG:
    """Test SVG creation of box generators.
    Just test generators which have a default output without an input requirement.
    Uses SVG files stored next to each generator source file as reference.
    """

    configPath = Path(__file__).parent.parent / 'examples.yml'
    with open(configPath) as ff:
        configData = yaml.safe_load(ff)

    all_generators = boxes.generators.getAllBoxGenerators()
    generators_by_name = {b.__name__: b for b in all_generators.values()}

    notTestGenerators = set()
    brokenGenerators = set()
    additionalTests = []
    # find the __ALL__ generator in examples.yml
    for ii, box_settings in enumerate(configData.get("Boxes")):
        if box_settings.get("box_type") == "__ALL__":
            notTestGenerators = set(box_settings.get("skipGenerators", []))
            brokenGenerators = set(box_settings.get("brokenGenerators", []))
        else:
            additionalTests.append(box_settings)
    avoidGenerator = notTestGenerators | brokenGenerators

    @staticmethod
    def _gen_dir_and_stem(generator: type[boxes.Boxes]) -> tuple[Path, str]:
        """Return (directory, stem) for the generator source file.

        Handles both the legacy flat layout (``xxx.py``) and the new
        per-generator folder layout where the source is ``xxx/__init__.py``.
        """
        gen_file = Path(inspect.getfile(generator))
        if gen_file.name == "__init__.py":
            # New layout: boxes/generators/<cat>/<stem>/__init__.py
            return gen_file.parent, gen_file.parent.name
        # Legacy flat layout: boxes/generators/<cat>/<stem>.py
        return gen_file.parent, gen_file.stem

    @staticmethod
    def _reference_svg(generator: type[boxes.Boxes]) -> Path:
        """Reference SVG lives in the generator folder (same stem, .svg)."""
        gen_dir, stem = TestSVG._gen_dir_and_stem(generator)
        return gen_dir / f"{stem}.svg"

    @staticmethod
    def _reference_svg_hashed(generator: type[boxes.Boxes], hash8: str) -> Path:
        """Hash-suffixed reference SVG lives in the generator folder."""
        gen_dir, stem = TestSVG._gen_dir_and_stem(generator)
        return gen_dir / f"{stem}_{hash8}.svg"

    def test_generators_available(self) -> None:
        assert len(self.all_generators) != 0

    # svgcheck currently do not allow inkscape custom tags.
    # @staticmethod
    # def is_valid_svg(file_path: str) -> bool:
    #     result = subprocess.run(['svgcheck', file_path], capture_output=True, text=True)
    #     return "INFO: File conforms to SVG requirements." in result.stdout

    @staticmethod
    def get_additional_test_args_hash(generator_settings):
        # this needs to stay synchronized with boxes_main example_output_fname_formatter
        boxArgs = []
        for kk, vv in generator_settings["args"].items():
            boxArgs.append(f"--{kk}={vv}")
        argsHash = hashlib.sha1(" ".join(sorted(boxArgs)).encode("utf-8")).hexdigest()
        return boxArgs, argsHash

    @staticmethod
    def is_valid_xml_by_lxml(xml_string: str) -> bool:
        try:
            etree.fromstring(xml_string)
            return True
        except etree.XMLSyntaxError:
            return False

    @staticmethod
    def idfunc(val) -> str:
        return f"{val.__name__}"

    @staticmethod
    def idfunc_args(generator_idx) -> str:
        generator_settings = TestSVG.additionalTests[generator_idx]
        boxName = generator_settings["box_type"]
        boxArgs, argsHash = TestSVG.get_additional_test_args_hash(generator_settings)
        boxArgs = " ". join(boxArgs)
        return f"{boxName}_{generator_idx}_{argsHash}_{boxArgs}"

    @pytest.mark.parametrize(
        "generator",
        all_generators.values(),
        ids=idfunc.__func__,
    )
    def test_default_generator(self, generator: type[boxes.Boxes], capsys) -> None:
        boxName = generator.__name__
        if boxName in self.avoidGenerator:
            pytest.skip("Skipped generator")
        box = generator()
        box.parseArgs("")
        box.metadata["reproducible"] = True
        box.open()
        box.render()
        boxData = box.close()

        out, err = capsys.readouterr()

        assert 100 < boxData.__sizeof__(), "No data generated."
        assert 0 == len(out), "Console output generated."
        assert 0 == len(err), "Console error generated."

        # Use external library lxml as cross-check.
        assert self.is_valid_xml_by_lxml(boxData.getvalue()) is True, "Invalid XML according to library lxml."

        file = Path(__file__).resolve().parent / 'data' / (boxName + '.svg')
        file.write_bytes(boxData.getvalue())

        # Use reference SVG stored next to the generator source file.
        referenceData = self._reference_svg(generator)
        assert referenceData.exists() is True, "Reference file for comparison does not exist."
        assert referenceData.is_file() is True, "Reference file for comparison does not exist."
        assert referenceData.read_bytes() == boxData.getvalue(), "SVG files are not equal. If change is intended, please update example files."

    if additionalTests:
        @pytest.mark.parametrize(
            "generator_idx",
            range(len(additionalTests)),
            ids=idfunc_args.__func__,
        )
        def test_additonal_generator(self, generator_idx, capsys) -> None:
            generator_settings = self.additionalTests[generator_idx]
            boxType = generator_settings.get("box_type", None)
            if boxType is None:
                pytest.fail("box_type must be provided for additional tests")
            generator = self.generators_by_name.get(boxType, None)
            if generator is None:
                pytest.fail(f"{boxType} is not a valid generator {self.all_generators.keys()}")
            boxName = generator_settings.get("name", boxType)
            box = generator()

            boxArgs, argsHash = TestSVG.get_additional_test_args_hash(generator_settings)

            box.parseArgs(boxArgs)
            box.metadata["reproducible"] = True
            box.metadata["args_hash"] = argsHash
            box.open()
            box.render()
            boxData = box.close()

            out, err = capsys.readouterr()

            assert 100 < boxData.__sizeof__(), "No data generated."
            assert 0 == len(out), "Console output generated."
            assert 0 == len(err), "Console error generated."

            # Use external library lxml as cross-check.
            assert self.is_valid_xml_by_lxml(boxData.getvalue()) is True, "Invalid XML according to library lxml."

            file = Path(__file__).resolve().parent / 'data' / (boxName + '_' + argsHash[0:8] + '.svg')
            file.write_bytes(boxData.getvalue())

            # Use reference SVG stored next to the generator source file.
            referenceData = self._reference_svg_hashed(generator, argsHash[0:8])
            assert referenceData.exists() is True, "Reference file for comparison does not exist."
            assert referenceData.is_file() is True, "Reference file for comparison does not exist."
            assert referenceData.read_bytes() == boxData.getvalue(), "SVG files are not equal. If change is intended, please update example files."

    def test_abondoned_examples(self, capsys) -> None:
        # Load the args hash for all defined additionalTests
        validTests = set()
        for generator_settings in self.additionalTests:
            boxType = generator_settings.get("box_type", None)
            if boxType is None:
                continue
            generator = self.generators_by_name.get(boxType, None)
            if generator is None:
                continue
            gen_dir, stem = TestSVG._gen_dir_and_stem(generator)
            boxArgs, argsHash = TestSVG.get_additional_test_args_hash(generator_settings)
            validTests.add((stem, argsHash[0:8]))

        # Scan all generator source directories for hash-suffixed SVG files
        gen_dirs: set[Path] = set()
        for cls in self.generators_by_name.values():
            try:
                gen_dir, _ = TestSVG._gen_dir_and_stem(cls)
                gen_dirs.add(gen_dir)
            except TypeError:
                pass

        exampleFiles: set[tuple[str, str]] = set()
        for gen_dir in gen_dirs:
            for svg_file in gen_dir.glob('*.svg'):
                if re.match(r'^.+_[0-9a-f]{8}$', svg_file.stem):
                    stem_part, hash_part = svg_file.stem.rsplit('_', 1)
                    exampleFiles.add((stem_part, hash_part))

        extraExamples = exampleFiles - validTests
        if extraExamples:
            pytest.fail(f"{len(extraExamples)} extra files found: {extraExamples}")
