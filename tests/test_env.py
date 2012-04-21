from unittest import TestCase
from bytehold.env import *


class EnvironmentTest(TestCase):
    def test_singleton(self):
        env1 = Environment()
        env2 = Environment()
        self.assertEqual(id(env1), id(env2))

    def test___init__(self):
        env = Environment(value1=1, value2=2, value3=3)
        self.assertEqual(env.config['value1'], 1)
        self.assertEqual(env.config['value2'], 2)
        self.assertEqual(env.config['value3'], 3)

    def test_name(self):
        env = Environment()
        with self.assertRaises(InvalidConfiguration):
            env.name()
        env.extend(name='test')
        self.assertEqual(env.name(), 'test')
        env.extend(name='test2')
        self.assertEqual(env.name(), 'test2')

    def test_command_rsync(self):
        env = Environment()
        self.assertEqual(env.command_rsync(), RSYNC_COMMAND)
        env.extend(rsync_command='test')
        self.assertEqual(env.command_rsync(), 'test')
        env.extend(rsync_command='test2')
        self.assertEqual(env.command_rsync(), 'test2')

    def test_remote_host(self):
        env = Environment()
        with self.assertRaises(InvalidConfiguration):
            env.remote_host()
        env.extend(remote_host='test')
        self.assertEqual(env.remote_host(), 'test')
        env.extend(remote_host='test2')
        self.assertEqual(env.remote_host(), 'test2')

    def test_remote_path(self):
        env = Environment()
        with self.assertRaises(InvalidConfiguration):
            env.remote_path()
        env.extend(remote_path='test')
        self.assertEqual(env.remote_path(), os.path.join('test', env.name()))
        env.extend(remote_path='test2')
        self.assertEqual(env.remote_path(), os.path.join('test2', env.name()))

    def test_command_compress(self):
        env = Environment()
        self.assertEqual(env.command_compress(), COMPRESS_COMMAND)
        env.extend(compress_cmd='test')
        self.assertEqual(env.command_compress(), 'test')
        env.extend(compress_cmd='test2')
        self.assertEqual(env.command_compress(), 'test2')

    def test_command_scp(self):
        env = Environment()
        self.assertEqual(env.command_scp(), SCP_COMMAND)
        env.extend(scp_cmd='test')
        self.assertEqual(env.command_scp(), 'test')
        env.extend(scp_cmd='test2')
        self.assertEqual(env.command_scp(), 'test2')

    def test_extend(self):
        env = Environment()
        self.assertFalse("testkey" in env.config)
        env.extend(testkey='testvalue')
        self.assertEqual(env.config['testkey'], 'testvalue')
        env.extend(testkey='testvalue2')
        self.assertEqual(env.config['testkey'], 'testvalue2')
