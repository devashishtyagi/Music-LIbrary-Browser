Music Library Browser
=====================

## Description ##
A web2py application that supports browsing and searching of [musicbrainz](http://musicbrainz.org) data. It also let's you create playlists and export them to csv format. The application requires a local image of the the music brainz database server possibly in postgres. You can find instructions on how to create a locally hosted musicbrainz server [here](https://github.com/metabrainz/musicbrainz-server).
## Features ##
* Searching of music library corpus by artist name, album name and recording name. The searching is improved by use of GIN indexes on terms in the database.
* Lookup of relevant information about artists, albums and recordings group. The album art for various albums is obtained through cover art archive.
* Rate various albums and artists. Both the user personal rating (can be changed) and the aggregate rating of all the users is displayed on an album's information page.
* The home page displays a list of top rated albums based on users' ratings.
* Users can create playlists and add desired songs to them.



