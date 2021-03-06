import shutil, tempfile, pkg_resources
from unittest import TestCase, skip
from medacy.data import Dataset
from medacy.tools import Annotations, InvalidAnnotationError
from os.path import join
from medacy.tests.tools.converters.con_test_data.con_test import con_text, source_text as con_source_text
from medacy.tests.tools.sample_data.ann_samples import ann_text_one, ann_text_two, ann_text_one_modified, \
    ann_text_one_source


class TestAnnotation(TestCase):

    @classmethod
    def setUpClass(cls):
        """Loads END dataset and writes files to temp directory"""
        cls.test_dir = tempfile.mkdtemp()  # set up temp directory
        cls.dataset, _, meta_data = Dataset.load_external('medacy_dataset_end')
        cls.entities = meta_data['entities']
        cls.ann_files = []
        # fill directory of training files
        for data_file in cls.dataset.get_data_files():
            file_name, raw_text, ann_text = (data_file.file_name, data_file.raw_path, data_file.ann_path)
            cls.ann_files.append(file_name + '.ann')

        with open(join(cls.test_dir, "broken_ann_file.ann"), 'w') as f:
            f.write("This is clearly not a valid ann file")

        cls.ann_file_path_one = join(cls.test_dir, "ann1.ann")
        with open(cls.ann_file_path_one, "w+") as f:
            f.write(ann_text_one)

        cls.ann_file_path_two = join(cls.test_dir, "ann1.ann")
        with open(cls.ann_file_path_one, "w+") as f:
            f.write(ann_text_two)

        cls.ann_file_path_modified = join(cls.test_dir, "ann_mod.ann")
        with open(cls.ann_file_path_modified, "w+") as f:
            f.write(ann_text_one_modified)

        cls.ann_file_path_source = join(cls.test_dir, "ann_source.txt")
        with open(cls.ann_file_path_source, "w+") as f:
            f.write(ann_text_one_source)

    @classmethod
    def tearDownClass(cls):
        """Removes test temp directory and deletes all files"""
        pkg_resources.cleanup_resources()
        shutil.rmtree(cls.test_dir)  # remove temp directory and delete all files

    def test_init_from_dict(self):
        """Tests initalization from a dictionary"""
        annotations = Annotations({'entities': {}, 'relations': []})
        self.assertIsInstance(annotations, Annotations)

    def test_init_from_ann_file(self):
        """Tests initialization from valid ann file"""
        annotations = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        self.assertIsNotNone(annotations.get_entity_annotations())

    def test_init_from_invalid_dict(self):
        """Tests initialization from invalid dict file"""
        with self.assertRaises(InvalidAnnotationError):
            Annotations({})

    def test_init_from_invalid_ann(self):
        """Tests initialization from invalid annotation file"""
        with self.assertRaises(FileNotFoundError):
            Annotations(join(self.dataset.get_data_directory(), self.ann_files[0][:-1]), annotation_type='ann')

    def test_init_from_non_dict_or_string(self):
        """Tests initialization from non-dictionary or string"""
        with self.assertRaises(TypeError):
            Annotations(list(), annotation_type='ann')

    def test_init_from_broken_ann_file(self):
        """Tests initialization from a correctly structured but ill-formated ann file"""
        with self.assertRaises(InvalidAnnotationError):
            Annotations(join(self.test_dir, "broken_ann_file.ann"), annotation_type='ann')

    def test_ann_conversions(self):
        """Tests converting and un-converting a valid Annotations object to an ANN file."""
        annotations = Annotations(join(self.dataset.get_data_directory(),self.ann_files[0]), annotation_type='ann')
        annotations.to_ann(write_location=join(self.test_dir,"intermediary.ann"))
        annotations2 = Annotations(join(self.test_dir,"intermediary.ann"), annotation_type='ann')
        self.assertEqual(annotations.get_entity_annotations(return_dictionary=True),
                         annotations2.get_entity_annotations(return_dictionary=True))

    def test_get_entity_annotations_dict(self):
        """Tests the validity of the annotation dict"""
        annotations = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        self.assertIsInstance(annotations.get_entity_annotations(return_dictionary=True), dict)

    def test_get_entity_annotations_list(self):
        """Tests the validity of annotation list"""
        annotations = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        self.assertIsInstance(annotations.get_entity_annotations(), list)

    def test_good_con_data(self):
        """Tests to see if valid con data can be used to instantiate an Annotations object."""
        with open(join(self.test_dir, "test_con.con"), 'w+') as c,\
                open(join(self.test_dir, "test_con_text.txt"), 'w+') as t:
            c.write(con_text)
            t.write(con_source_text)

            annotations = Annotations(c.name, annotation_type='con', source_text_path=t.name)
            self.assertIsInstance(annotations.get_entity_annotations(), list)

    def test_bad_con_data(self):
        """Tests to see if invalid con data will raise InvalidAnnotationError."""
        with open(join(self.test_dir, "bad_con.con"), 'w+') as c,\
                open(join(self.test_dir, "test_con_text.txt"), 'w+') as t:
            c.write("This string wishes it was a valid con file.")
            t.write("It doesn't matter what's in this file as long as it exists.")

            Annotations(c.name, annotation_type='con', source_text_path=t.name)
            self.assertRaises(InvalidAnnotationError)

    def test_good_con_data_without_text(self):
        """Tests to see if not having a source text file will raise FileNotFoundError."""
        with open(join(self.test_dir, "test_con.con"), 'w+') as c:
                c.write(con_text)
                with self.assertRaises(FileNotFoundError):
                    Annotations(c.name, annotation_type='con', source_text_path=None)

    def test_difference(self):
        """Tests that when a given Annotations object uses the diff() method with another Annotations object created
        from the same source file, that it returns an empty list."""
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        annotations2 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        result = annotations1.difference(annotations2)
        self.assertFalse(result)

    def test_different_file_diff(self):
        """Tests that when two different files are used in the diff() method, either ValueError is raised (because the
        two Annotations cannot be compared) or that the output is a list with more than one value."""
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        annotations2 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[1]), annotation_type='ann')
        result = annotations1.difference(annotations2)
        self.assertGreater(len(result), 0)

    def test_compute_ambiguity(self):
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        annotations2 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        label, start, end, text = annotations2.get_entity_annotations()[0]
        annotations2.add_entity('incorrect_label', start, end, text)
        self.assertEqual(len(annotations1.compute_ambiguity(annotations2)), 1)

    def test_confusion_matrix(self):
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        annotations2 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[1]), annotation_type='ann')
        annotations1.add_entity(*annotations2.get_entity_annotations()[0])

        self.assertEqual(len(annotations1.compute_confusion_matrix(annotations2, self.entities)[0]), len(self.entities))
        self.assertEqual(len(annotations1.compute_confusion_matrix(annotations2, self.entities)), len(self.entities))

    @skip("Not currently working")
    def test_intersection(self):
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        annotations2 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[1]), annotation_type='ann')
        annotations1.add_entity(*annotations2.get_entity_annotations()[0])
        annotations1.add_entity(*annotations2.get_entity_annotations()[1])
        self.assertEqual(annotations1.intersection(annotations2),
                         set([annotations2.get_entity_annotations()[0],
                         annotations2.get_entity_annotations()[1]])
                         )

    def test_compute_counts(self):
        annotations1 = Annotations(join(self.dataset.get_data_directory(), self.ann_files[0]), annotation_type='ann')
        self.assertIsInstance(annotations1.compute_counts(), dict)
