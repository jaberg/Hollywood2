"""
Python code for loading Hollywood2 meta-data into Python objects.

The dataset is a pair of video classification problems: Actions and Scenes.

The Actions dataset  
TODO ... groups, sizes of groups, number of dual labelings...

The Scenes dataset 
TODO ...groups, sizes of groups, number of dual labelings...

Image resolutions are not fixed across the dataset.
The number of rows varies from 224 to 576.
The number of columns varies from 480 to 720.
The aspect ratio is also not fixed, it varies from 1.25 to 2.5.

"""

import sys, os

import pyffmpeg

action_names = ['AnswerPhone', 'DriveCar', 'Eat', 
        'FightPerson' , 'GetOutCar', 'HandShake',
        'HugPerson', 'Kiss', 'Run', 'SitDown',
        'SitUp', 'StandUp']

scene_names = ['EXT-house', 'EXT-road', 'INT-bedroom', 'INT-car', 'INT-hotel',
        'INT-kitchen', 'INT-living-room', 'INT-office',
        'INT-restaurant', 'INT-shop']

def load_basic_info(avidir, vid_info=True):
    """
    Return a dictionary of dictionaries.

    Each [internal] dictionary corresponds to a clip from the avidir.
    The keys in each [internal] dictionary are:

        name: the name of the file in avidir (without extension)
        path: the full path of the file in avidir
        label: a string describing the subject of the video.
               For actions this is one of the `action_names`.
               For scenes this is one of the `scene_names`.
        group: one of 'train', 'test', 'autotrain'
        resolution: (height, width)
        duration: number of frames
        shots: first frames of shots within the clip

    The outer dictionary maps name -> internal dictionary
    """

    clips = {}

    for filename in os.listdir(avidir):
        # initialize the list of clips with just name and path
        name = filename[:-4]
        clip = dict(
                path=os.path.join(avidir,filename), 
                name=name)

        print clip['name']

        # set the group based on the filename
        if 'cliptrain' in filename:
            clip['group'] = 'train'
        elif 'cliptest' in filename:
            clip['group'] = 'test'
        elif 'clipauto' in filename:
            clip['group'] = 'autotrain'
        else:
            assert False

        clips[name] = clip

    return clips

def add_label_info(clips, labeldir, labels, group_names):
    for label in labels:
        for group in group_names:
            filename = '%s_%s.txt' % (label, group)

            for line in open(os.path.join(labeldir, filename)):
                name, one_or_neg1 = line.split()
                clips[name].setdefault('label', {})[label] = (one_or_neg1 == '1')

    # assert that every clip got a full set of labels
    for name, clip in clips.iteritems():
        assert len(clip['label']) == len(labels)

def add_shots_info(clips, shotdir):
    for name, clip in clips.iteritems():
        clip['shots'] = [int(f) 
                for f in open(os.path.join(shotdir, name+'.sht')).read().split()]
        print clip['shots']

def add_vid_info(clips):
    for name, clip in clips.iteritems():

        # set the resolution and duration by opening the file with ffmpeg
        reader = pyffmpeg.FFMpegReader(False)
        reader.open(clip['path'], { 
                'video1':(0, -1, {
                    'dest_height':-1,
                    'dest_width':-1,
                    'outputmode':pyffmpeg.OUTPUTMODE_NUMPY})})#, pyffmpeg.TS_VIDEO_)
        video_track = reader.get_tracks()[0]

        clip['duration'] = video_track.duration()
        clip['resolution'] = video_track.get_size()

def build(root):

    """

    Return a pair of lists.
    The first is a list of movies in the Actions set
    The second is a list of movies in the Scenes set 

    """
    actions = load_basic_info( os.path.join(root, 'AVIClips',) )
    add_label_info(actions, os.path.join(root, 'ClipSets',),
            action_names, ['train', 'test', 'autotrain'])
    add_shots_info(actions, os.path.join(root, 'ShotBounds',))
    add_vid_info(actions)

    scenes = load_basic_info( os.path.join(root, 'AVIClipsScenes',))
    add_label_info(scenes, os.path.join(root, 'ClipSetsScenes',), 
            scene_names, ['test', 'autotrain'])
    add_shots_info(scenes, os.path.join(root, 'ShotBoundsScenes',))
    add_vid_info(scenes)

    return actions, scenes

if __name__ == '__main__':
    actions, scenes = build(sys.argv[1])

    import cPickle
    f = open(sys.argv[2], 'w')
    cPickle.dump(actions, f)
    cPickle.dump(scenes, f)
    f.close()

