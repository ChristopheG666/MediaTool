var iTunesApp = WScript.CreateObject("iTunes.Application");
var i = 1;
for (i = 1; i <= iTunesApp.SelectedTracks.Count; i++)
{
var track = iTunesApp.SelectedTracks.Item(i);
track.LongDescription = track.description;
}