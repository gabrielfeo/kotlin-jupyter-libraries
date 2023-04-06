#!/usr/bin/env python3

from check_renovate_matches import main
from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest
from unittest import mock
from pathlib import Path
import io

LIB1_DESCRIPTOR = '''
    {
        "properties": [
            {"name": "version", "value": "0.3.2"},
            {"name": "applyColorScheme", "value": "true"}
        ],
        "dependencies": [
            "org.nd4j:nd4j-api:$version"
        ]
    }
'''

LIB2_DESCRIPTOR = '''
    {
        "properties": {
            "spark": "3.3.1",
            "scala": "2.13",
            "v": "1.2.3",
            "freemarker": "2.3.29"
        },
        "dependencies": [
            "org.jetbrains.kotlinx.spark:jupyter_$spark_$scala:$v",
            "org.freemarker:freemarker:$freemarker",
            "example:lib:1.0"
        ]
    }
'''


class TestCheckRenovateMatches(unittest.TestCase):

    def tearDown(self):
        self.tempdir.cleanup()
        self.renovate_log.close()

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_given_empty_log_then_fails(self, stderr: io.StringIO):
        self.setup_descriptors_and_log(log_content='')
        with self.assertRaises(SystemExit) as context:
            main(self.descriptors_dir, renovate_debug_log=self.renovate_log)
        self.assertEqual(context.exception.code, 1)
        stderr = stderr.getvalue()
        self.assertIn('org.freemarker:freemarker', stderr)
        self.assertIn('org.nd4j:nd4j-api', stderr)
        self.assertIn('org.jetbrains.kotlinx.spark:jupyter_3.3.1_2.13', stderr)
        self.assertIn('example:lib', stderr)

    def setup_descriptors_and_log(self, log_content):
        self.renovate_log = NamedTemporaryFile('w+')
        self.renovate_log.write(log_content)
        self.renovate_log.flush()
        self.renovate_log.seek(0)
        self.tempdir = TemporaryDirectory()
        self.descriptors_dir = Path(self.tempdir.name)
        with open(self.descriptors_dir/'lib1.json', 'w') as lib1:
            lib1.write(LIB1_DESCRIPTOR)
        with open(self.descriptors_dir/'lib2.json', 'w') as lib2:
            lib2.write(LIB2_DESCRIPTOR)

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_given_log_with_some_missing_packages_then_fails(self, stderr: io.StringIO):
        self.setup_descriptors_and_log(log_content='''
            2023-03-30T13:46:13.0262830Z DEBUG: logs
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up org.freemarker:freemarker in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
            2023-03-30T13:46:13.0262830Z DEBUG: more logs
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up org.nd4j:nd4j-api in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up example:lib in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
        ''')
        with self.assertRaises(SystemExit) as context:
            main(self.descriptors_dir, renovate_debug_log=self.renovate_log)
        self.assertEqual(context.exception.code, 1)
        stderr = stderr.getvalue()
        self.assertIn('org.jetbrains.kotlinx.spark:jupyter_3.3.1_2.13', stderr)
        self.assertNotIn('org.freemarker:freemarker', stderr)
        self.assertNotIn('org.nd4j:nd4j-api', stderr)
        self.assertNotIn('example:lib', stderr)

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_given_log_with_no_missing_package_then_succeeds(self, stderr: io.StringIO):
        self.setup_descriptors_and_log(log_content='''
            2023-03-30T13:46:13.0262830Z DEBUG: logs
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up org.freemarker:freemarker in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
            2023-03-30T13:46:13.0262830Z DEBUG: more logs
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up org.nd4j:nd4j-api in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up example:lib in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
            2023-03-30T13:46:13.0262830Z DEBUG: Looking up org.jetbrains.kotlinx.spark:jupyter_3.3.1_2.13 in repository https://repo.maven.apache.org/maven2/ (repository=kotlin/example)
        ''')
        try:
            main(self.descriptors_dir, renovate_debug_log=self.renovate_log)
            self.assertEqual(stderr.getvalue(), '')
        except SystemExit as exit:
            msg = f"Unexpected system exit {exit.code}. Stderr: {stderr.getvalue()}"
            raise AssertionError(msg)


if __name__ == '__main__':
    unittest.main()
