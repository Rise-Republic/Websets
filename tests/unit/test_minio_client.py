import unittest
from app.storage.minio_client import tenant_object_name

class TestMinioClientHelpers(unittest.TestCase):
    def test_tenant_object_name(self):
        self.assertEqual(tenant_object_name("t1", "file.txt"), "t1/file.txt")

if __name__ == "__main__":
    unittest.main()
