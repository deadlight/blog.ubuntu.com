# Core
import unittest
import time
from urllib.parse import urlparse, urlunparse

# Local
import app
from api import get
from helpers import ignore_warnings


test_content = 'Ubuntu and Canonical are registered'

working_uris = [
    '/',  # Homepage
    '/?category=articles',  # Category filter on homepage
    '/cloud-and-server?page=2',  # Group page
    '/cloud-and-server?page=999',  # Group empty page
    '/cloud-and-server?category=white-papers',  # whitepapers page
    '/cloud-and-server?category=case-studies&page=2',  # Group & category page
    '/cloud-and-server?category=case-studies&page=999',  # empty page
    '/press-centre',  # Press centre
    '/topics/maas?page=2',  # Topic page
    '/topics/maas?page=999',  # Topic empty page
    '/author/canonical',  # Author page
    '/search',  # Search (empty)
    '/search?q=lxd',  # Search for a term
    '/tag/security',  # Tag page
    '/archives',  # All archives
    '/archives?page=2',  # Archives by year
    '/archives?year=2018&month=1&page=2',  # Archives by year and month
    '/archives?year=2018&month=1&page=999',  # empty page
    '/archives?year=100&month=24',  # Non existent dates
    '/archives?year=2099',  # Empty archive year
    '/archives?year=2099&month=12',  # Empty archive month
    '/archives?group=cloud-and-server&year=2099&page=2',  # Empty group archive
    '/2018/01/24/meltdown-spectre-and-ubuntu-what-you-need-to-know',  # article
    '/2017/08/31/openstack-weekly-update-august-31-2017',  # article no author
]

missing_uris = [
    '/non-existent-group',  # Unknown group
    '/𝐢𝜛𝒔𝞪𝓃ҽ-𝘶𝔯l',  # Weird UTF-8 chars in URL
    '/2018', '/2018/01', '/2018/01/24',  # Date URLs
    '/cloud-and-server/non-existent-category',  # Unknown category page
    '/press-centre/2099',  # Press centre, erroneous year
    '/press-centre/fake-url',  # Press centre, fake suffix
    '/topics/non-existent',  # Missing topic
    '/author',  # No author selected
    '/author/non-existent-author',  # Missing author
    '/search/fake-suffix?q=nothing',  # Search, fake suffix
    '/tag',  # No tag selected
    '/tag/fake-tag',  # Non-existent tag
    '/archives/201',  # Archive, non-year suffix
    '/archives/2018/24',  # Non existent archive month
    '/archives/cloud-and-server',  # Group archive, no selected year
    '/archives/cloud-and-server/2018/02?page=2',  # Group archive, year + month
    '/archives/non-existent-group/2018',  # Non existent group archive
    '/2018/01/24/a-missing-article',  # article
]


@ignore_warnings(ResourceWarning)
def _get_posts():
    response = get(
        'posts',
        {
            '_embed': True,
            'per_page': 3,
            'group': "1479,1666"
        }
    )

    return response.json()


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    def test_cache(self):
        # Warm cache
        initial_posts = _get_posts()

        # Make a request with the cache warmed
        start = time.time()
        subsequent_posts = _get_posts()
        request_time = time.time() - start

        assert type(initial_posts) == list
        assert initial_posts == subsequent_posts
        assert request_time < 0.1

    def test_working_urls(self):
        """
        Check a bunch of URLs for basic success
        """

        print(" Testing working URLs:")

        for uri in working_uris:
            print('  - ' + uri + ' ... ', end='')
            self._check_basic_page(uri)
            print('done')

    @ignore_warnings(ResourceWarning)
    def test_missing_urls(self):
        """
        Check a bunch of URLs for basic success
        """

        print(" Testing missing URLs:")

        for uri in missing_uris:
            print('  - ' + uri + ' ... ', end='')
            response = self.app.get(uri)
            assert response.status_code == 404
            assert test_content in str(response.data)
            print('done')

    @ignore_warnings(ResourceWarning)
    def _get_check_slash_normalisation(self, uri):
        """
        Given a basic app path (e.g. '/page'), check that any trailing
        slashes are removed with a 302 redirect, and return the response
        for the principal URL
        """

        # Check trailing slashes trigger redirect
        parsed_uri = urlparse(uri)
        slash_uri = urlunparse(parsed_uri._replace(path=parsed_uri.path + '/'))
        redirect_response = self.app.get(slash_uri)
        assert redirect_response.status_code == 302

        url = "http://localhost" + uri
        assert redirect_response.headers.get('Location') == url

        return self.app.get(uri)

    @ignore_warnings(ResourceWarning)
    def _check_basic_page(self, uri):
        """
        Check that a URI returns an HTML page that will redirect to remove
        slashes, returns a 200 and contains the standard footer text
        """

        if urlparse(uri).path == '/':
            response = self.app.get(uri)
        else:
            response = self._get_check_slash_normalisation(uri)

        assert response.status_code == 200
        assert test_content in str(response.data)

        return response


if __name__ == '__main__':
    unittest.main()
